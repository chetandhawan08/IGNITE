import io
import os
import time
import numpy as np
import pandas as pd

from .anomaly import detect_anomalies
from .ai import ai_summarize
from .plotting import plot_flux, plot_series
from .config import last_dataset_context, TELESCOPE_AUTHORS


def _is_transient_download_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    transient_tokens = (
        "connection aborted",
        "connection reset",
        "connectionerror",
        "timeout",
        "temporarily unavailable",
        "winerror 10053",
        "10053",
    )
    return any(token in msg for token in transient_tokens)


def _download_with_retries(search, retries: int = 3, delay_seconds: float = 1.5):
    for attempt in range(1, retries + 1):
        try:
            return search.download()
        except Exception as exc:
            if attempt >= retries or not _is_transient_download_error(exc):
                raise
            time.sleep(delay_seconds * attempt)

    return None


# ── CSV pipeline ─────────────────────────────────────────────────────────────

def run_csv_pipeline(file_bytes: bytes, filename: str,
                     column_index: int = 0) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {"error": f"Could not read CSV: {e}"}

    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.empty:
        return {"error": "No numeric columns found in CSV."}

    columns = list(numeric_df.columns)
    if column_index < 0 or column_index >= len(columns):
        column_index = 0

    column = columns[column_index]
    series = numeric_df[column].dropna()
    if series.empty:
        return {"error": "Selected column has no valid data."}

    predictions = detect_anomalies(series)
    anomaly_mask = predictions == -1
    x_values = np.arange(len(series))
    y_values = series.to_numpy()

    summary = {
        "source":             filename,
        "column":             column,
        "dataset_size":       len(series),
        "anomalies_detected": int(anomaly_mask.sum()),
        "mean":               round(float(series.mean()), 4),
        "std":                round(float(series.std()), 4),
        "min":                round(float(series.min()), 4),
        "max":                round(float(series.max()), 4),
    }

    last_dataset_context["data"] = summary
    last_dataset_context["source"] = f"CSV file: {filename}, column: {column}"

    ai_summary = ai_summarize(summary)
    plot_result = plot_series(
        x_values, y_values, anomaly_mask,
        ylabel=column, title=f"Anomaly Detection — {column}",
    )

    return {
        "summary":    summary,
        "ai_summary": ai_summary,
        "columns":    columns,
        **plot_result,
    }


# ── Search available telescope data for a target ─────────────────────────────

def search_planet_datasets(target: str) -> dict:
    """
    Returns all available missions / cadences for a given target name.
    Used to populate the telescope selector before downloading.
    """
    try:
        import lightkurve as lk
    except Exception:
        return {"error": "lightkurve is not installed."}

    try:
        results = lk.search_lightcurve(target)
        if results is None or len(results) == 0:
            return {"error": f"No datasets found for '{target}'."}

        table = results.table
        missions = []
        seen = set()
        for row in table:
            mission  = str(row.get("mission",  row.get("#mission",  ""))).strip()
            author   = str(row.get("author",   row.get("#author",   ""))).strip()
            cadence  = str(row.get("exptime",  row.get("t_exptime", ""))).strip()
            label = f"{mission} — {author} ({cadence}s)"
            key   = f"{author}||{cadence}"
            if key not in seen:
                seen.add(key)
                missions.append({
                    "label":   label,
                    "author":  author,
                    "cadence": cadence,
                    "mission": mission,
                })

        return {"target": target, "missions": missions}
    except Exception as e:
        return {"error": str(e)}


# ── Lightkurve pipeline ───────────────────────────────────────────────────────

def run_lightkurve_pipeline(target: str, telescope_key: str = "any",
                             author_override: str = None,
                             show_transit_regions: bool = True) -> dict:
    try:
        import lightkurve as lk
    except Exception:
        return {"error": "lightkurve is not installed. Run: pip install lightkurve"}

    # Resolve author
    if author_override:
        author = author_override if author_override != "any" else None
    else:
        author = TELESCOPE_AUTHORS.get(telescope_key, None)

    try:
        kwargs = {}
        if author:
            kwargs["author"] = author

        search = lk.search_lightcurve(target, **kwargs)
        if search is None or len(search) == 0:
            return {"error": f"No light curve data found for '{target}'" +
                    (f" with author '{author}'" if author else "") + "."}

        download_retries = int(os.getenv("IGNITE_DOWNLOAD_RETRIES", "3"))
        lightcurve = _download_with_retries(search, retries=max(1, download_retries))
        if lightcurve is None:
            return {"error": "Could not download dataset. Try another planet or telescope."}

        lightcurve = lightcurve.remove_nans().normalize()
        time = lightcurve.time.value
        flux = lightcurve.flux.value

        # Collect mission metadata if available
        mission_info = getattr(lightcurve, "meta", {})
        mission_name = mission_info.get("MISSION",
                       mission_info.get("TELESCOP", telescope_key.upper()))

    except Exception as e:
        return {
            "error": (
                "Could not download dataset. "
                f"Network may have interrupted the transfer ({e}). "
                "Please retry, or try another telescope/target."
            )
        }

    predictions = detect_anomalies(flux)
    anomaly_mask = predictions == -1
    transit_mask = flux < np.median(flux)

    # Transit depth calculation
    transit_flux = flux[transit_mask]
    transit_depth = round(float(1.0 - np.min(transit_flux)), 6) if transit_mask.any() else 0.0

    summary = {
        "planet":             target,
        "mission":            mission_name,
        "dataset_size":       len(flux),
        "anomalies_detected": int(anomaly_mask.sum()),
        "transit_dips":       int(transit_mask.sum()),
        "transit_depth":      transit_depth,
        "flux_mean":          round(float(np.mean(flux)), 6),
        "flux_std":           round(float(np.std(flux)), 6),
    }

    last_dataset_context["data"] = summary
    last_dataset_context["source"] = f"Lightkurve — {target} ({mission_name})"

    ai_summary = ai_summarize(summary)
    plot_result = plot_flux(
        time, flux, anomaly_mask, transit_mask,
        title=f"Exoplanet Transit Detection — {target} ({mission_name})",
        show_transit_regions=show_transit_regions,
    )

    return {
        "summary":    summary,
        "ai_summary": ai_summary,
        **plot_result,
    }

import io
import base64
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Keep style dictionary but stop forcing custom colors
STYLE = {
    "bg": None,
    "surface": None,
    "grid": None,
    "flux": None,
    "transit": '#008000',
    "anomaly": None,
    "highlight": None,
    "text": None,
    "text_dim": None,
}


def _apply_plot_style(fig, ax):
    # Use default matplotlib style (no overrides)
    pass


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        bbox_inches="tight",
        dpi=130,
        facecolor=fig.get_facecolor(),
    )
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def plot_flux(time, flux, anomaly_mask, transit_mask=None, title="", show_transit_regions=True) -> dict:
    """
    Returns dict with:
      - plot: base64 PNG of full light curve
      - transit_plot: base64 PNG zoomed on transit dips (if any)
      - raw_data: {time, flux, anomaly_indices, transit_indices} for frontend interactive plot
    """
    fig, ax = plt.subplots(figsize=(13, 5))
    _apply_plot_style(fig, ax)

    # Default matplotlib color
    ax.plot(time, flux, linewidth=0.95, alpha=0.95, label="Flux", zorder=2)

    # Remove filled transit regions (too cluttered)
    if transit_mask is not None and transit_mask.any():
        ax.scatter(
            time[transit_mask],
            flux[transit_mask],
            s=10,
            label="Transit dips",
            zorder=4,
            alpha=0.8,
        )

    ax.scatter(
        time[anomaly_mask],
        flux[anomaly_mask],
        s=16,
        color="red",
        label="Anomalies",
        zorder=5,
        marker="x",
        linewidths=0.9,
    )

    median_flux = float(np.median(flux))
    ax.axhline(
        median_flux,
        linewidth=0.75,
        linestyle="--",
        alpha=0.75,
        label="Median flux",
    )

    ax.set_xlabel("Time (BKJD / BTJD)", fontsize=9)
    ax.set_ylabel("Normalized Flux", fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="semibold", pad=10)
    ax.legend(fontsize=8)

    fig.tight_layout(pad=1.5)
    full_plot = _fig_to_base64(fig)

    transit_plot = None
    if transit_mask is not None and transit_mask.any():
        transit_indices = np.where(transit_mask)[0]
        deepest_idx = transit_indices[np.argmin(flux[transit_indices])]

        time_range = time[-1] - time[0]
        window = max(time_range * 0.05, 1.0)
        t_center = time[deepest_idx]
        mask_zoom = (time >= t_center - window) & (time <= t_center + window)

        if mask_zoom.sum() > 10:
            fig2, ax2 = plt.subplots(figsize=(9, 4))
            _apply_plot_style(fig2, ax2)

            tz = time[mask_zoom]
            fz = flux[mask_zoom]

            ax2.plot(tz, fz, linewidth=1.0, label="Flux", zorder=3)
            ax2.scatter(
                tz[transit_mask[mask_zoom]],
                fz[transit_mask[mask_zoom]],
                s=14,
                label="Transit dips",
                zorder=4,
            )

            min_flux = float(np.min(fz))
            depth = round((1.0 - min_flux) * 100, 4)
            ax2.annotate(
                f"Depth: {depth}%",
                xy=(t_center, min_flux),
                xytext=(t_center, min_flux - 0.005),
                fontsize=8,
                ha="center",
                arrowprops=dict(arrowstyle="->", lw=0.7),
            )

            ax2.axhline(
                median_flux,
                linewidth=0.75,
                linestyle="--",
                alpha=0.75,
                label="Median flux",
            )

            ax2.set_xlabel("Time (BKJD / BTJD)", fontsize=9)
            ax2.set_ylabel("Normalized Flux", fontsize=9)
            ax2.set_title(f"Transit Dip - Zoomed View | {title}", fontsize=10, fontweight="semibold", pad=10)
            ax2.legend(fontsize=8)

            fig2.tight_layout(pad=1.5)
            transit_plot = _fig_to_base64(fig2)

    step = max(1, len(time) // 2000)
    raw_data = {
        "time": time[::step].tolist(),
        "flux": flux[::step].tolist(),
        "median_flux": median_flux,
        "anomaly_indices": np.where(anomaly_mask[::step])[0].tolist(),
        "transit_indices": (np.where(transit_mask[::step])[0].tolist() if transit_mask is not None else []),
    }

    return {
        "plot": full_plot,
        "transit_plot": transit_plot,
        "raw_data": raw_data,
    }


def plot_series(x, y, anomaly_mask, xlabel="Index", ylabel="Value", title="") -> dict:
    fig, ax = plt.subplots(figsize=(13, 5))
    _apply_plot_style(fig, ax)

    ax.plot(x, y, linewidth=0.95, alpha=0.95, label=ylabel, zorder=2)
    ax.scatter(
        x[anomaly_mask],
        y[anomaly_mask],
        s=18,
        color="red",
        label="Anomalies",
        zorder=4,
        marker="x",
        linewidths=0.95,
    )

    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=11, fontweight="semibold", pad=10)
    ax.legend(fontsize=8)

    fig.tight_layout(pad=1.5)

    step = max(1, len(x) // 2000)
    raw_data = {
        "time": x[::step].tolist(),
        "flux": y[::step].tolist(),
        "median_flux": float(np.median(y)),
        "anomaly_indices": np.where(anomaly_mask[::step])[0].tolist(),
        "transit_indices": [],
    }

    return {
        "plot": _fig_to_base64(fig),
        "transit_plot": None,
        "raw_data": raw_data,
    }

from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import IsolationForest


PLANETS = [
    "K2-18b",
    "Kepler-10b",
    "Kepler-22b",
    "Kepler-452b",
    "WASP-12b",
    "HAT-P-7b",
]


app = FastAPI(title="AI-Powered Time-Series Anomaly Detection Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


latest_result: dict[str, Any] = {
    "status": "No data",
    "message": "No data",
    "dataset_type": None,
    "chart": None,
    "summary": None,
    "csv_export": None,
}


class DetectExoplanetRequest(BaseModel):
    planet: str
    contamination: float = 0.01


def detect_anomalies(series, contamination=0.01):
    data = np.asarray(series, dtype=float).reshape(-1, 1)
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
    )
    predictions = model.fit_predict(data)
    return predictions


def clamp_contamination(value: float) -> float:
    return min(max(float(value), 0.01), 0.2)


def build_csv_chart(x_values, y_values, anomaly_mask, column_name):
    return {
        "data": [
            {
                "x": x_values.tolist(),
                "y": y_values.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": column_name,
                "line": {"color": "blue"},
            },
            {
                "x": x_values[anomaly_mask].tolist(),
                "y": y_values[anomaly_mask].tolist(),
                "type": "scatter",
                "mode": "markers",
                "name": "Anomalies",
                "marker": {"color": "red", "size": 8},
            },
        ],
        "layout": {
            "title": "Anomaly Detection - External Dataset",
            "xaxis": {"title": "Index"},
            "yaxis": {"title": column_name},
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
        },
    }


def build_exoplanet_chart(time, flux, anomaly_mask, transit_mask, planet):
    return {
        "data": [
            {
                "x": time.tolist(),
                "y": flux.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Flux",
                "line": {"color": "blue"},
            },
            {
                "x": time[anomaly_mask].tolist(),
                "y": flux[anomaly_mask].tolist(),
                "type": "scatter",
                "mode": "markers",
                "name": "Anomalies",
                "marker": {"color": "red", "size": 8},
            },
        ],
        "layout": {
            "title": f"Exoplanet Transit Detection - {planet}",
            "xaxis": {"title": "Time"},
            "yaxis": {"title": "Normalized Flux"},
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
        },
    }


def set_latest_result(
    *,
    status: str,
    message: str,
    dataset_type: str | None = None,
    chart: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    csv_export: str | None = None,
):
    latest_result["status"] = status
    latest_result["message"] = message
    latest_result["dataset_type"] = dataset_type
    latest_result["chart"] = chart
    latest_result["summary"] = summary
    latest_result["csv_export"] = csv_export


def export_csv(dataframe: pd.DataFrame) -> str:
    return dataframe.to_csv(index=False)


@app.get("/")
def root():
    return {
        "project": "AI-Powered Time-Series Anomaly Detection Platform for Exoplanet Transit & CSV Data",
        "planets": PLANETS,
    }


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        set_latest_result(status="error", message="Invalid file")
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        content = await file.read()
        dataframe = pd.read_csv(BytesIO(content))
    except Exception as exc:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file") from exc

    numeric_df = dataframe.select_dtypes(include=np.number)
    if numeric_df.empty:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    first_numeric_column = numeric_df.columns[0]
    series = numeric_df[first_numeric_column].dropna()
    if series.empty:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    payload = {
        "status": "success",
        "message": "File uploaded successfully",
        "filename": file.filename,
        "rows": int(len(series)),
        "column": first_numeric_column,
    }
    set_latest_result(status="success", message=payload["message"], dataset_type="csv")
    return payload


@app.post("/detect")
async def detect_csv(
    file: UploadFile = File(...),
    contamination: float = Form(0.01),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        set_latest_result(status="error", message="Invalid file")
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        content = await file.read()
        df = pd.read_csv(BytesIO(content))
    except Exception as exc:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file") from exc

    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.empty:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    first_numeric_column = numeric_df.columns[0]
    series = numeric_df[first_numeric_column].dropna()
    if series.empty:
        set_latest_result(status="error", message="Invalid CSV file")
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    contamination = clamp_contamination(contamination)
    predictions = detect_anomalies(series, contamination=contamination)
    anomaly_mask = predictions == -1

    x_values = np.arange(len(series))
    y_values = series.to_numpy()

    result_df = pd.DataFrame(
        {
            "index": x_values,
            first_numeric_column: y_values,
            "prediction": predictions,
            "is_anomaly": anomaly_mask,
        }
    )

    summary = {
        "anomalies_detected": int(anomaly_mask.sum()),
        "transit_dips_detected": "No",
        "dataset_size": int(len(series)),
        "column_used": first_numeric_column,
        "contamination": contamination,
    }
    chart = build_csv_chart(x_values, y_values, anomaly_mask, first_numeric_column)

    response = {
        "status": "success",
        "message": "Detection completed",
        "dataset_type": "csv",
        "summary": summary,
        "chart": chart,
        "download_name": "csv_detection_results.csv",
    }
    set_latest_result(
        status="success",
        message=response["message"],
        dataset_type="csv",
        chart=chart,
        summary=summary,
        csv_export=export_csv(result_df),
    )
    return response


@app.post("/detect-exoplanet")
def detect_exoplanet(request: DetectExoplanetRequest):
    try:
        import lightkurve as lk
    except Exception as exc:
        set_latest_result(status="error", message="lightkurve is not installed.")
        raise HTTPException(status_code=500, detail="lightkurve is not installed.") from exc

    if request.planet not in PLANETS:
        set_latest_result(status="error", message="Invalid planet selection.")
        raise HTTPException(status_code=400, detail="Invalid planet selection.")

    try:
        search = lk.search_lightcurve(request.planet)
        lightcurve = search.download()
        if lightcurve is None:
            set_latest_result(status="error", message="Could not download dataset")
            raise HTTPException(status_code=404, detail="Could not download dataset")

        lightcurve = lightcurve.remove_nans().normalize()
        time = lightcurve.time.value
        flux = lightcurve.flux.value
    except HTTPException:
        raise
    except Exception as exc:
        set_latest_result(status="error", message="Could not download dataset")
        raise HTTPException(status_code=500, detail="Could not download dataset") from exc

    contamination = clamp_contamination(request.contamination)
    predictions = detect_anomalies(flux, contamination=contamination)
    anomaly_mask = predictions == -1
    transit_mask = flux < np.median(flux)

    result_df = pd.DataFrame(
        {
            "time": time,
            "flux": flux,
            "prediction": predictions,
            "is_anomaly": anomaly_mask,
            "is_transit_dip": transit_mask,
        }
    )

    summary = {
        "anomalies_detected": int(anomaly_mask.sum()),
        "transit_dips_detected": "Yes" if bool(transit_mask.sum()) else "No",
        "dataset_size": int(len(flux)),
        "planet": request.planet,
        "contamination": contamination,
    }
    chart = build_exoplanet_chart(time, flux, anomaly_mask, transit_mask, request.planet)

    response = {
        "status": "success",
        "message": "Detection completed",
        "dataset_type": "exoplanet",
        "summary": summary,
        "chart": chart,
        "download_name": f"{request.planet}_detection_results.csv",
    }
    set_latest_result(
        status="success",
        message=response["message"],
        dataset_type="exoplanet",
        chart=chart,
        summary=summary,
        csv_export=export_csv(result_df),
    )
    return response


@app.get("/results")
def get_results():
    return {
        "status": latest_result["status"],
        "message": latest_result["message"],
        "dataset_type": latest_result["dataset_type"],
        "summary": latest_result["summary"],
    }


@app.get("/visualization")
def get_visualization():
    if latest_result["chart"] is None:
        raise HTTPException(status_code=404, detail="No data")
    return latest_result["chart"]


@app.get("/download-results")
def download_results():
    if latest_result["csv_export"] is None:
        raise HTTPException(status_code=404, detail="No data")
    return {
        "status": "success",
        "filename": "detection_results.csv",
        "content": latest_result["csv_export"],
    }

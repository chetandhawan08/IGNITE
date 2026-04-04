import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


PLANETS = [
    "K2-18b",
    "Kepler-10b",
    "Kepler-22b",
    "Kepler-452b",
    "WASP-12b",
    "HAT-P-7b",
]


def detect_anomalies(series, contamination=0.01):
    data = np.asarray(series, dtype=float).reshape(-1, 1)
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
    )
    predictions = model.fit_predict(data)
    return predictions


def run_lightkurve_pipeline():
    try:
        import lightkurve as lk
    except Exception:
        print("\nlightkurve is not installed.\n")
        return

    print("\nAvailable Exoplanets:\n")
    for index, planet in enumerate(PLANETS, start=1):
        print(f"{index}. {planet}")

    choice = input("\nEnter planet number: ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(PLANETS)):
        print("\nInvalid planet selection.\n")
        return

    target = PLANETS[int(choice) - 1]

    try:
        print("\nDownloading...\n")
        search = lk.search_lightcurve(target)
        lightcurve = search.download()
        if lightcurve is None:
            print("Could not download dataset")
            print("Try another planet")
            return

        lightcurve = lightcurve.remove_nans().normalize()
        time = lightcurve.time.value
        flux = lightcurve.flux.value
    except Exception:
        print("Could not download dataset")
        print("Try another planet")
        return

    predictions = detect_anomalies(flux)
    anomaly_mask = predictions == -1
    transit_mask = flux < np.median(flux)

    plt.figure(figsize=(12, 6))
    plt.plot(time, flux, color="blue", label="Flux")
    plt.scatter(
        time[transit_mask],
        flux[transit_mask],
        color="green",
        s=20,
        label="Transit dips",
    )
    plt.scatter(
        time[anomaly_mask],
        flux[anomaly_mask],
        color="red",
        s=28,
        label="Anomalies",
    )
    plt.xlabel("Time")
    plt.ylabel("Normalized Flux")
    plt.title(f"Exoplanet Transit Detection - {target}")
    plt.legend()
    plt.tight_layout()
    plt.show()


def run_csv_pipeline():
    file_path = input("\nEnter CSV file path: ").strip()
    if not file_path:
        print("\nInvalid CSV file\n")
        return

    try:
        df = pd.read_csv(file_path)
    except Exception:
        print("\nInvalid CSV file\n")
        return

    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.empty:
        print("\nInvalid CSV file\n")
        return

    first_numeric_column = numeric_df.columns[0]
    series = numeric_df[first_numeric_column].dropna()
    if series.empty:
        print("\nInvalid CSV file\n")
        return

    predictions = detect_anomalies(series)
    anomaly_mask = predictions == -1

    x_values = np.arange(len(series))
    y_values = series.to_numpy()

    plt.figure(figsize=(12, 6))
    plt.plot(x_values, y_values, color="blue", label=first_numeric_column)
    plt.scatter(
        x_values[anomaly_mask],
        y_values[anomaly_mask],
        color="red",
        s=28,
        label="Anomalies",
    )
    plt.xlabel("Index")
    plt.ylabel(first_numeric_column)
    plt.title("Anomaly Detection - External Dataset")
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    while True:
        print("\nSelect option:\n")
        print("1. Use Lightkurve Exoplanet Dataset")
        print("2. Load External CSV Dataset")
        print("3. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            run_lightkurve_pipeline()
        elif choice == "2":
            run_csv_pipeline()
        elif choice == "3":
            print("\nExiting...\n")
            break
        else:
            print("\nInvalid choice\n")


if __name__ == "__main__":
    main()

const API_BASE = "http://127.0.0.1:8000";

const csvFileInput = document.getElementById("csvFile");
const uploadStatus = document.getElementById("uploadStatus");
const planetStatus = document.getElementById("planetStatus");
const resultStatus = document.getElementById("resultStatus");
const contaminationSlider = document.getElementById("contaminationSlider");
const contaminationValue = document.getElementById("contaminationValue");
const planetSelect = document.getElementById("planetSelect");
const anomaliesCount = document.getElementById("anomaliesCount");
const transitCount = document.getElementById("transitCount");
const datasetSize = document.getElementById("datasetSize");

contaminationSlider.addEventListener("input", () => {
    contaminationValue.textContent = contaminationSlider.value;
});

document.getElementById("uploadButton").addEventListener("click", uploadFile);
document.getElementById("detectCsvButton").addEventListener("click", detectCSV);
document.getElementById("detectPlanetButton").addEventListener("click", detectPlanet);
document.getElementById("downloadButton").addEventListener("click", downloadResults);

async function uploadFile() {
    const file = csvFileInput.files[0];
    if (!file) {
        uploadStatus.textContent = "Invalid file";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    uploadStatus.textContent = "Running detection...";

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Invalid CSV file");
        }
        uploadStatus.textContent = `${data.message} | ${data.rows} rows | ${data.column}`;
        resultStatus.textContent = "File uploaded successfully";
    } catch (error) {
        uploadStatus.textContent = error.message;
        resultStatus.textContent = error.message;
    }
}

async function detectCSV() {
    const file = csvFileInput.files[0];
    if (!file) {
        uploadStatus.textContent = "Invalid file";
        return;
    }

    uploadStatus.textContent = "Running detection...";
    resultStatus.textContent = "Running detection...";

    const formData = new FormData();
    formData.append("file", file);
    formData.append("contamination", contaminationSlider.value);

    try {
        const response = await fetch(`${API_BASE}/detect`, {
            method: "POST",
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Invalid CSV file");
        }
        plotGraph(data.chart);
        updateResults(data.summary, data.message);
        uploadStatus.textContent = "Detection completed";
    } catch (error) {
        uploadStatus.textContent = error.message;
        resultStatus.textContent = error.message;
    }
}

async function detectPlanet() {
    planetStatus.textContent = "Running detection...";
    resultStatus.textContent = "Running detection...";

    try {
        const response = await fetch(`${API_BASE}/detect-exoplanet`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                planet: planetSelect.value,
                contamination: Number(contaminationSlider.value),
            }),
        });
        const data = await response.json();
        if (!response.ok) {
            if (data.detail === "Could not download dataset") {
                throw new Error("Could not download dataset. Try another planet");
            }
            throw new Error(data.detail || "Could not download dataset");
        }
        plotGraph(data.chart);
        updateResults(data.summary, data.message);
        planetStatus.textContent = "Detection completed";
    } catch (error) {
        planetStatus.textContent = error.message;
        resultStatus.textContent = error.message;
    }
}

function detectPlanetLegacy() {
    return detectPlanet();
}

function plotGraph(chart) {
    Plotly.newPlot("graph", chart.data, chart.layout, {
        responsive: true,
        displaylogo: false,
    });
}

function updateResults(summary, message) {
    anomaliesCount.textContent = summary.anomalies_detected;
    transitCount.textContent = summary.transit_dips_detected;
    datasetSize.textContent = `${summary.dataset_size} rows`;
    resultStatus.textContent = message;
}

async function downloadResults() {
    try {
        const response = await fetch(`${API_BASE}/download-results`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "No data");
        }

        const blob = new Blob([data.content], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = data.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    } catch (error) {
        resultStatus.textContent = error.message;
    }
}

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PLANETS = [
    "K2-18b",
    "Kepler-10b",
    "Kepler-22b",
    "Kepler-452b",
    "WASP-12b",
    "HAT-P-7b",
    "55 Cancri e",
    "GJ 1214b",
    "HD 209458b",
    "TRAPPIST-1b",
    "TRAPPIST-1e",
    "TRAPPIST-1f",
    "LHS 1140b",
    "TOI-700d",
    "Proxima Centauri b",
    "CoRoT-7b",
    "Kepler-16b",
    "Kepler-62f",
    "Kepler-186f",
    "WASP-76b",
]

# Maps frontend telescope key -> lightkurve author string (None = any)
TELESCOPE_AUTHORS = {
    "any":      None,
    "kepler":   "Kepler",
    "k2":       "K2",
    "tess":     "SPOC",
    "tess_qlp": "QLP",
}

# Stores last loaded dataset for chat context (mirrors CLI global)
last_dataset_context = {"data": None, "source": None}

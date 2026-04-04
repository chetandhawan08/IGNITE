from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os

from .config import PLANETS, TELESCOPE_AUTHORS, last_dataset_context
from .pipelines import run_csv_pipeline, run_lightkurve_pipeline, search_planet_datasets
from .ai import ai_chat

app = FastAPI(title="Ignite AI Exoplanet Observatory")

# In-memory conversation history (single-session, mirrors CLI)
_conversation_history: List[dict] = []

# ── Static frontend ──────────────────────────────────────────────────────────

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "favicon.svg"),
        media_type="image/svg+xml",
    )


# ── Config ───────────────────────────────────────────────────────────────────

@app.get("/api/planets")
def get_planets():
    return {"planets": PLANETS}


@app.get("/api/telescopes")
def get_telescopes():
    labels = {
        "any":      "Any (Auto-select)",
        "kepler":   "Kepler",
        "k2":       "K2",
        "tess":     "TESS (SPOC)",
        "tess_qlp": "TESS (QLP)",
    }
    return {"telescopes": [{"key": k, "label": v}
                           for k, v in labels.items()]}


# ── Planet search (returns available missions before download) ────────────────

@app.get("/api/search")
async def search_planet(target: str, telescope: str = "any"):
    if not target.strip():
        raise HTTPException(status_code=400, detail="Target name required.")
    result = search_planet_datasets(target.strip())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Exoplanet pipeline ────────────────────────────────────────────────────────

@app.post("/api/exoplanet")
async def exoplanet_pipeline(
    planet: str = Form(...),
    telescope: str = Form("any"),
    author_override: str = Form(None),
    show_transit_regions: bool = Form(True),
):
    if not planet.strip():
        raise HTTPException(status_code=400, detail="Planet name required.")
    result = run_lightkurve_pipeline(
        target=planet.strip(),
        telescope_key=telescope,
        author_override=author_override or None,
        show_transit_regions=show_transit_regions,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── CSV pipeline ──────────────────────────────────────────────────────────────

@app.post("/api/csv")
async def csv_pipeline(
    file: UploadFile = File(...),
    column_index: int = Form(0),
):
    file_bytes = await file.read()
    result = run_csv_pipeline(file_bytes, file.filename, column_index)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    response = ai_chat(req.message, _conversation_history)
    _conversation_history.append({"role": "user",      "content": req.message})
    _conversation_history.append({"role": "assistant", "content": response})

    return {
        "response":        response,
        "dataset_context": last_dataset_context["source"],
    }


@app.post("/api/chat/clear")
def chat_clear():
    _conversation_history.clear()
    return {"message": "Conversation history cleared."}


@app.get("/api/chat/context")
def chat_context():
    return {
        "source": last_dataset_context["source"],
        "data":   last_dataset_context["data"],
    }

import uvicorn


if __name__ == "__main__":

    import os

    host = os.getenv("IGNITE_HOST", "0.0.0.0")
    port = int(os.getenv("IGNITE_PORT", "8000"))
    reload_enabled = os.getenv("IGNITE_RELOAD", "0") == "1"

    uvicorn.run("backend.main:app", host=host, port=port, reload=reload_enabled)

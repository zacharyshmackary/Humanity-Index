from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
from pathlib import Path

app = FastAPI()
WEB = Path(__file__).parent / "web"
DATA = Path(__file__).parent / "data_local"

app.mount("/web", StaticFiles(directory=WEB), name="web")

@app.get("/", response_class=HTMLResponse)
def root():
    return (WEB / "index.html").read_text()

@app.get("/api/latest")
def latest():
    f = DATA / "latest.json"
    return JSONResponse(json.loads(f.read_text())) if f.exists() else {"error":"no data yet"}

@app.get("/api/index")
def index():
    f = DATA / "index_series.json"
    return JSONResponse(json.loads(f.read_text())) if f.exists() else {"error":"no data yet"}

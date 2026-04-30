"""
AgriData CM — Backend Principal
FastAPI + SQLite + Analyse Python
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uvicorn
import os

from api.routes_producteur import router as producteur_router
from api.routes_parcelle import router as parcelle_router
from api.routes_phyto import router as phyto_router
from api.routes_marche import router as marche_router
from api.routes_climat import router as climat_router
from api.routes_analyse import router as analyse_router
from api.routes_export import router as export_router
from db.database import init_db

app = FastAPI(
    title="AgriData CM",
    description="Collecte & Analyse de Données Agricoles — Cameroun",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Inclure les routes
app.include_router(producteur_router, prefix="/api/producteurs", tags=["Producteurs"])
app.include_router(parcelle_router, prefix="/api/parcelles", tags=["Parcelles"])
app.include_router(phyto_router, prefix="/api/phyto", tags=["Phytosanitaire"])
app.include_router(marche_router, prefix="/api/marche", tags=["Marchés"])
app.include_router(climat_router, prefix="/api/climat", tags=["Climatologie"])
app.include_router(analyse_router, prefix="/api/analyse", tags=["Analyses"])
app.include_router(export_router, prefix="/api/export", tags=["Export"])

@app.on_event("startup")
async def startup():
    init_db()
    os.makedirs("exports", exist_ok=True)
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/data/uploads"))
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok", "app": "AgriData CM v1.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

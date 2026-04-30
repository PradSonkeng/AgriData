"""Routes Phytosanitaire"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from db.database import get_db
import shutil, os, uuid
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "static/uploads"

@router.get("/")
def list_phyto(id_parcelle: int = None):
    conn = get_db()
    if id_parcelle:
        rows = conn.execute("SELECT * FROM phyto WHERE id_parcelle=? ORDER BY created_at DESC", (id_parcelle,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM phyto ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/")
async def create_phyto(
    id_parcelle: int = Form(None),
    organe: str = Form(None),
    symptome: str = Form(None),
    severite: str = Form(None),
    culture: str = Form(None),
    description: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    altitude: float = Form(None),
    photo: UploadFile = File(None)
):
    photo_path = None
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        fname = f"{uuid.uuid4()}.{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(fpath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        photo_path = f"/static/uploads/{fname}"

    exif_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO phyto (id_parcelle,organe,symptome,severite,culture,description,
        photo_path,latitude,longitude,altitude,exif_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (id_parcelle,organe,symptome,severite,culture,description,
          photo_path,latitude,longitude,altitude,exif_date))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "photo_path": photo_path, "message": "Relevé enregistré"}

@router.get("/stats/resume")
def stats_phyto():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM phyto").fetchone()[0]
    par_symptome = conn.execute("""
        SELECT symptome, COUNT(*) as n FROM phyto GROUP BY symptome ORDER BY n DESC
    """).fetchall()
    conn.close()
    return {"total_releves": total, "par_symptome": [dict(r) for r in par_symptome]}

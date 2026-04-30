"""Routes Climatologie"""
from fastapi import APIRouter
from db.database import get_db
from db.models import ClimatCreate

router = APIRouter()

@router.get("/")
def list_climat(localite: str = None):
    conn = get_db()
    if localite:
        rows = conn.execute("SELECT * FROM climatologie WHERE localite=? ORDER BY mois_annee DESC", (localite,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM climatologie ORDER BY mois_annee DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/")
def create_climat(c: ClimatCreate):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO climatologie (localite,mois_annee,pluviometrie_mm,jours_pluie,
        intensite_max,temp_moyenne,humidite_moy,evenement,notes)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (c.localite,c.mois_annee,c.pluviometrie_mm,c.jours_pluie,
          c.intensite_max,c.temp_moyenne,c.humidite_moy,c.evenement,c.notes))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "message": "Relevé climatologique enregistré"}

@router.get("/stats/resume")
def stats_climat():
    conn = get_db()
    rows = conn.execute("""
        SELECT mois_annee, AVG(pluviometrie_mm) as pluie_moy,
        AVG(temp_moyenne) as temp_moy, COUNT(*) as n
        FROM climatologie GROUP BY mois_annee ORDER BY mois_annee DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

from fastapi import APIRouter, HTTPException
from db.database import get_db
from db.models import ParcelleCreate
import json, math

router = APIRouter()

def shoelace(coords):
    """Calcul de superficie via la formule de Shoelace (Gauss)"""
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        lat1, lon1 = math.radians(coords[i][1]), math.radians(coords[i][0])
        lat2, lon2 = math.radians(coords[j][1]), math.radians(coords[j][0])
        area += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
    area = abs(area) * 6378137 ** 2 / 2
    return round(area / 10000, 4)  # m² → hectares

@router.get("/")
def list_parcelles(id_producteur: int = None):
    conn = get_db()
    if id_producteur:
        rows = conn.execute(
            "SELECT p.*, pr.nom as nom_producteur FROM parcelles p "
            "JOIN producteurs pr ON p.id_producteur=pr.id WHERE p.id_producteur=?",
            (id_producteur,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.*, pr.nom as nom_producteur FROM parcelles p "
            "JOIN producteurs pr ON p.id_producteur=pr.id ORDER BY p.created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/")
def create_parcelle(p: ParcelleCreate):
    # Calcul automatique superficie si GeoJSON fourni
    superficie = p.superficie_ha
    if p.geojson and not superficie:
        try:
            geo = json.loads(p.geojson)
            coords = geo["coordinates"][0]
            superficie = shoelace(coords)
        except Exception:
            pass

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO parcelles (id_producteur,geojson,superficie_ha,type_sol,
        culture_principale,methode_mesure,type_terrain,observations)
        VALUES (?,?,?,?,?,?,?,?)
    """, (p.id_producteur, p.geojson, superficie, p.type_sol,
          p.culture_principale, p.methode_mesure, p.type_terrain, p.observations))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "superficie_ha": superficie, "message": "Parcelle enregistrée"}

@router.get("/stats/resume")
def stats_parcelles():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM parcelles").fetchone()[0]
    surface = conn.execute("SELECT SUM(superficie_ha) FROM parcelles").fetchone()[0] or 0
    par_culture = conn.execute("""
        SELECT culture_principale, COUNT(*) as n, SUM(superficie_ha) as total_ha
        FROM parcelles GROUP BY culture_principale ORDER BY n DESC
    """).fetchall()
    conn.close()
    return {"total_parcelles": total, "surface_totale_ha": round(surface, 2),
            "par_culture": [dict(r) for r in par_culture]}

@router.get("/{pid}")
def get_parcelle(pid: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM parcelles WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Parcelle introuvable")
    return dict(row)

@router.post("/calculer-superficie")
def calculer_superficie(geojson: dict):
    """Calcul de superficie à partir d'un polygone GeoJSON"""
    try:
        coords = geojson["coordinates"][0]
        ha = shoelace(coords)
        return {"superficie_ha": ha, "superficie_m2": round(ha * 10000, 1)}
    except Exception as e:
        raise HTTPException(400, f"GeoJSON invalide: {e}")

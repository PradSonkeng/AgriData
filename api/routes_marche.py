"""Routes Prix Marché"""
from fastapi import APIRouter, HTTPException
from db.database import get_db
from db.models import PrixMarcheCreate
from typing import List

router = APIRouter()

@router.get("/")
def list_prix(marche: str = None, produit: str = None, limit: int = 200):
    conn = get_db()
    q = "SELECT * FROM prix_marche WHERE 1=1"
    params = []
    if marche:
        q += " AND marche=?"; params.append(marche)
    if produit:
        q += " AND produit=?"; params.append(produit)
    q += " ORDER BY date_releve DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/")
def create_prix(p: PrixMarcheCreate):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO prix_marche (marche,date_releve,produit,prix_fcfa) VALUES (?,?,?,?)",
        (p.marche, p.date_releve, p.produit, p.prix_fcfa)
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "message": "Prix enregistré"}

@router.post("/batch")
def create_prix_batch(prix_list: List[PrixMarcheCreate]):
    conn = get_db()
    ids = []
    for p in prix_list:
        cur = conn.execute(
            "INSERT INTO prix_marche (marche,date_releve,produit,prix_fcfa) VALUES (?,?,?,?)",
            (p.marche, p.date_releve, p.produit, p.prix_fcfa)
        )
        ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    return {"ids": ids, "count": len(ids)}

@router.get("/evolution/{produit}")
def evolution_prix(produit: str, marche: str = None):
    conn = get_db()
    q = "SELECT date_releve, marche, prix_fcfa FROM prix_marche WHERE produit=?"
    params = [produit]
    if marche:
        q += " AND marche=?"; params.append(marche)
    q += " ORDER BY date_releve ASC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/stats/resume")
def stats_marche():
    conn = get_db()
    rows = conn.execute("""
        SELECT produit, AVG(prix_fcfa) as prix_moyen, MIN(prix_fcfa) as prix_min,
        MAX(prix_fcfa) as prix_max, COUNT(*) as n_releves
        FROM prix_marche GROUP BY produit ORDER BY n_releves DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

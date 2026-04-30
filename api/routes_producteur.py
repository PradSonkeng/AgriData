from fastapi import APIRouter, HTTPException
from db.database import get_db
from db.models import ProducteurCreate

router = APIRouter()

@router.get("/")
def list_producteurs(skip: int = 0, limit: int = 100):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM producteurs ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, skip)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/")
def create_producteur(p: ProducteurCreate):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO producteurs (nom,telephone,localite,departement,sexe,age,
        taille_menage,actifs_agricoles,appartient_gic,nom_gic,culture_principale,consentement_rgpd)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (p.nom, p.telephone, p.localite, p.departement, p.sexe, p.age,
          p.taille_menage, p.actifs_agricoles, p.appartient_gic, p.nom_gic,
          p.culture_principale, p.consentement_rgpd))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return {"id": pid, "message": "Producteur enregistré"}

@router.get("/{pid}")
def get_producteur(pid: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM producteurs WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Producteur introuvable")
    return dict(row)

@router.put("/{pid}")
def update_producteur(pid: int, p: ProducteurCreate):
    conn = get_db()
    conn.execute("""
        UPDATE producteurs SET nom=?,telephone=?,localite=?,departement=?,sexe=?,age=?,
        taille_menage=?,actifs_agricoles=?,appartient_gic=?,nom_gic=?,culture_principale=?,
        consentement_rgpd=? WHERE id=?
    """, (p.nom,p.telephone,p.localite,p.departement,p.sexe,p.age,
          p.taille_menage,p.actifs_agricoles,p.appartient_gic,p.nom_gic,
          p.culture_principale,p.consentement_rgpd,pid))
    conn.commit()
    conn.close()
    return {"message": "Mis à jour"}

@router.delete("/{pid}")
def delete_producteur(pid: int):
    conn = get_db()
    conn.execute("DELETE FROM producteurs WHERE id=?", (pid,))
    conn.commit()
    conn.close()
    return {"message": "Supprimé"}

@router.get("/stats/resume")
def stats_producteurs():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM producteurs").fetchone()[0]
    gic = conn.execute("SELECT COUNT(*) FROM producteurs WHERE appartient_gic=1").fetchone()[0]
    cultures = conn.execute("""
        SELECT culture_principale, COUNT(*) as n FROM producteurs
        GROUP BY culture_principale ORDER BY n DESC
    """).fetchall()
    conn.close()
    return {"total": total, "dans_gic": gic, "cultures": [dict(r) for r in cultures]}

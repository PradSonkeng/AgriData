"""Routes Export — CSV / JSON / PDF"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, JSONResponse
from db.database import get_db
import csv, io, json
from datetime import datetime

router = APIRouter()

def _get_table(table: str, conn):
    allowed = {"producteurs","parcelles","phyto","prix_marche","climatologie","activites","analyses"}
    if table not in allowed:
        return []
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/csv/{table}")
def export_csv(table: str):
    conn = get_db()
    rows = _get_table(table, conn)
    conn.close()
    if not rows:
        return JSONResponse({"message": "Aucune donnée"})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    fname = f"agridata_{table}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"}
    )

@router.get("/json/{table}")
def export_json(table: str):
    conn = get_db()
    rows = _get_table(table, conn)
    conn.close()
    fname = f"agridata_{table}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    content = json.dumps(rows, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={fname}"}
    )

@router.get("/rapport-html")
def rapport_html():
    """Génère un rapport HTML complet"""
    conn = get_db()
    prods = conn.execute("SELECT COUNT(*) FROM producteurs").fetchone()[0]
    parcs = conn.execute("SELECT COUNT(*) FROM parcelles").fetchone()[0]
    surface = conn.execute("SELECT COALESCE(SUM(superficie_ha),0) FROM parcelles").fetchone()[0]
    prix = conn.execute("SELECT produit, AVG(prix_fcfa) as moy FROM prix_marche GROUP BY produit").fetchall()
    conn.close()
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    lignes_prix = "".join([f"<tr><td>{r['produit']}</td><td>{r['moy']:.0f} FCFA</td></tr>" for r in prix])
    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8">
<title>Rapport AgriData CM</title>
<style>
body{{font-family:Arial,sans-serif;margin:40px;color:#222}}
h1{{color:#16a34a}}h2{{color:#166534;border-bottom:2px solid #16a34a;padding-bottom:6px}}
table{{width:100%;border-collapse:collapse;margin:12px 0}}
th{{background:#16a34a;color:#fff;padding:8px}}td{{padding:8px;border:1px solid #ddd}}
.stat{{display:inline-block;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px 24px;margin:8px;text-align:center}}
.stat b{{font-size:28px;color:#16a34a;display:block}}
</style></head><body>
<h1>🌿 AgriData CM — Rapport de Collecte</h1>
<p>Généré le {date_str} | Région Centre, Cameroun</p>
<h2>Résumé Général</h2>
<div class="stat"><b>{prods}</b>Producteurs</div>
<div class="stat"><b>{parcs}</b>Parcelles</div>
<div class="stat"><b>{surface:.1f} ha</b>Surface totale</div>
<h2>Prix Moyens Marchés Locaux</h2>
<table><tr><th>Produit</th><th>Prix Moyen (FCFA/50kg)</th></tr>{lignes_prix}</table>
<p style="color:#888;font-size:12px">© AgriData CM — Plateforme de collecte et analyse agricole</p>
</body></html>"""
    return StreamingResponse(
        iter([html]),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=rapport_agridata.html"}
    )

@router.get("/sync-status")
def sync_status():
    conn = get_db()
    pending = {
        "producteurs": conn.execute("SELECT COUNT(*) FROM producteurs WHERE synced=0").fetchone()[0],
        "parcelles": conn.execute("SELECT COUNT(*) FROM parcelles WHERE synced=0").fetchone()[0],
        "prix_marche": conn.execute("SELECT COUNT(*) FROM prix_marche WHERE synced=0").fetchone()[0],
        "phyto": conn.execute("SELECT COUNT(*) FROM phyto WHERE synced=0").fetchone()[0],
    }
    conn.close()
    total = sum(pending.values())
    return {"total_pending": total, "details": pending}

@router.post("/marquer-synced/{table}")
def marquer_synced(table: str):
    allowed = {"producteurs","parcelles","prix_marche","phyto","climatologie"}
    if table not in allowed:
        return {"error": "Table non autorisée"}
    conn = get_db()
    conn.execute(f"UPDATE {table} SET synced=1 WHERE synced=0")
    conn.commit()
    conn.close()
    return {"message": f"Table {table} marquée comme synchronisée"}

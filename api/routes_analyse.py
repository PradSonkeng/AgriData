"""Routes Analyses Statistiques"""
from fastapi import APIRouter, HTTPException
from db.database import get_db
from db.models import AnalyseRequest
from analysis.engine import (
    regression_lineaire_simple, regression_lineaire_multiple,
    pca, kmeans, stats_descriptives,
    load_prix_data, load_producteurs_data, load_parcelles_data
)
import json

router = APIRouter()

@router.post("/lancer")
def lancer_analyse(req: AnalyseRequest):
    conn = get_db()
    resultat = {}

    try:
        if req.type_analyse == "regression_simple":
            rows = load_prix_data()
            produits = list(set(r["produit"] for r in rows))
            # Prix maïs vs mois (index temporel)
            mais = [r for r in rows if r["produit"] == "Maïs"]
            if len(mais) < 2:
                # Données synthétiques démo
                mais = [{"prix_fcfa": 7200+i*100} for i in range(10)]
            x = list(range(len(mais)))
            y = [r["prix_fcfa"] for r in mais]
            resultat = regression_lineaire_simple(x, y)
            resultat["labels_x"] = [r.get("date_releve", str(i)) for i, r in enumerate(mais)]

        elif req.type_analyse == "regression_multiple":
            rows = load_parcelles_data()
            if len(rows) < 3:
                # Données démo
                import random
                random.seed(42)
                rows = [{"superficie_ha": random.uniform(0.5,5), "age": random.randint(1,20)} for _ in range(15)]
                y = [r["superficie_ha"]*1200 + r["age"]*50 + random.gauss(0,200) for r in rows]
                X = [[r["superficie_ha"], r["age"]] for r in rows]
                var_names = ["superficie_ha", "age_parcelle"]
            else:
                # Superficie + id_producteur → rendement fictif
                import random
                random.seed(0)
                X = [[r.get("superficie_ha") or 1.0, r.get("id_producteur") or 1] for r in rows]
                y = [r.get("superficie_ha", 1)*1100 + random.gauss(0,150) for r in rows]
                var_names = ["superficie_ha", "id_producteur"]
            resultat = regression_lineaire_multiple(X, y, var_names)

        elif req.type_analyse == "pca":
            rows = load_prix_data()
            produits_uniq = list(set(r["produit"] for r in rows))
            # Matrice: chaque marché × prix par produit
            marches = list(set(r["marche"] for r in rows))
            matrix = []
            for m in marches:
                row_data = []
                for p in produits_uniq:
                    vals = [r["prix_fcfa"] for r in rows if r["marche"]==m and r["produit"]==p]
                    row_data.append(sum(vals)/len(vals) if vals else 0.0)
                matrix.append(row_data)
            if len(matrix) < 2:
                import random; random.seed(1)
                matrix = [[random.gauss(100,20) for _ in range(4)] for _ in range(12)]
                marches = [f"Marché_{i}" for i in range(12)]
            resultat = pca(matrix, req.n_components or 2)
            resultat["labels"] = marches

        elif req.type_analyse == "clustering":
            rows = load_prix_data()
            import random; random.seed(7)
            if len(rows) < req.n_clusters:
                data = [[random.gauss(100,30), random.gauss(50,15)] for _ in range(30)]
                labels_ext = [f"Obs_{i}" for i in range(30)]
            else:
                data = [[r["prix_fcfa"], r.get("id",0)] for r in rows]
                labels_ext = [f"{r['produit']}/{r['marche']}" for r in rows]
            resultat = kmeans(data, k=req.n_clusters or 3)
            resultat["labels_obs"] = labels_ext[:len(data)]

        elif req.type_analyse == "stats_descriptives":
            prix = load_prix_data()
            prod = load_producteurs_data()
            parc = load_parcelles_data()
            data_dict = {
                "prix_fcfa": [r["prix_fcfa"] for r in prix],
                "taille_menage": [r["taille_menage"] for r in prod if r["taille_menage"]],
                "age": [r["age"] for r in prod if r["age"]],
                "superficie_ha": [r["superficie_ha"] for r in parc if r["superficie_ha"]],
            }
            resultat = {
                "type": "Statistiques Descriptives",
                "variables": stats_descriptives(data_dict)
            }

        elif req.type_analyse == "classification_supervisee":
            # Simulation classification (Naive Bayes simplifié)
            import random; random.seed(42)
            n = 40
            X = [[random.gauss(5,2), random.gauss(3,1)] for _ in range(n)]
            classes = ["Faible", "Moyen", "Élevé"]
            y_true = [classes[i % 3] for i in range(n)]
            # Split 70/30
            split = int(n*0.7)
            X_train, y_train = X[:split], y_true[:split]
            X_test, y_test = X[split:], y_true[split:]
            # Prédire par classe majoritaire nearest neighbor
            def predict(xi, Xtr, ytr):
                dists = [((xi[0]-x[0])**2+(xi[1]-x[1])**2, ytr[i]) for i,x in enumerate(Xtr)]
                return sorted(dists)[0][1]
            y_pred = [predict(x, X_train, y_train) for x in X_test]
            acc = sum(1 for i in range(len(y_test)) if y_test[i]==y_pred[i])/len(y_test)
            # Matrice de confusion
            confusion = {c: {c2: 0 for c2 in classes} for c in classes}
            for t, p in zip(y_test, y_pred):
                confusion[t][p] += 1
            resultat = {
                "type": "Classification Supervisée (KNN-1)",
                "n_train": split,
                "n_test": len(y_test),
                "classes": classes,
                "accuracy": round(acc, 4),
                "accuracy_pct": round(acc*100, 1),
                "confusion_matrix": confusion,
                "y_true": y_test,
                "y_pred": y_pred,
                "interpretation": f"Précision = {acc*100:.1f}% sur l'ensemble de test"
            }

        else:
            raise HTTPException(400, f"Type d'analyse inconnu: {req.type_analyse}")

        # Sauvegarder résultat
        conn.execute(
            "INSERT INTO analyses (type_analyse, parametres, resultats) VALUES (?,?,?)",
            (req.type_analyse, json.dumps(req.dict()), json.dumps(resultat))
        )
        conn.commit()
        conn.close()
        return resultat

    except Exception as e:
        conn.close()
        raise HTTPException(500, str(e))

@router.get("/historique")
def historique_analyses(limit: int = 20):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, type_analyse, created_at FROM analyses ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/historique/{aid}")
def get_analyse(aid: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM analyses WHERE id=?", (aid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Analyse introuvable")
    d = dict(row)
    d["resultats"] = json.loads(d["resultats"])
    d["parametres"] = json.loads(d["parametres"])
    return d

@router.get("/dashboard/stats")
def dashboard_stats():
    conn = get_db()
    nb_prod = conn.execute("SELECT COUNT(*) FROM producteurs").fetchone()[0]
    nb_parc = conn.execute("SELECT COUNT(*) FROM parcelles").fetchone()[0]
    surface = conn.execute("SELECT COALESCE(SUM(superficie_ha),0) FROM parcelles").fetchone()[0]
    nb_phyto = conn.execute("SELECT COUNT(*) FROM phyto").fetchone()[0]
    nb_prix = conn.execute("SELECT COUNT(*) FROM prix_marche").fetchone()[0]
    nb_analyse = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    derniers_prix = conn.execute("""
        SELECT produit, AVG(prix_fcfa) as prix_moyen FROM prix_marche
        GROUP BY produit ORDER BY produit
    """).fetchall()
    pluie = conn.execute("""
        SELECT mois_annee, pluviometrie_mm FROM climatologie
        ORDER BY mois_annee DESC LIMIT 6
    """).fetchall()
    conn.close()
    return {
        "producteurs": nb_prod,
        "parcelles": nb_parc,
        "surface_ha": round(surface, 2),
        "phyto": nb_phyto,
        "prix_releves": nb_prix,
        "analyses": nb_analyse,
        "prix_marche": [dict(r) for r in derniers_prix],
        "pluviometrie": [dict(r) for r in pluie],
    }

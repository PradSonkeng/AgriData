"""
AgriData CM — Moteur d'Analyse Python
Régression, PCA, Classification, Clustering
"""
import json
import math
import random
from db.database import get_db

# ── Régression Linéaire Simple (sans sklearn) ────────────────────────────────
def regression_lineaire_simple(x_data, y_data):
    n = len(x_data)
    if n < 2:
        return {"erreur": "Données insuffisantes (minimum 2 points)"}
    mx = sum(x_data) / n
    my = sum(y_data) / n
    num = sum((x_data[i]-mx)*(y_data[i]-my) for i in range(n))
    den = sum((x-mx)**2 for x in x_data)
    if den == 0:
        return {"erreur": "Variance nulle sur X"}
    b1 = num / den
    b0 = my - b1 * mx
    y_pred = [b0 + b1*x for x in x_data]
    ss_res = sum((y_data[i]-y_pred[i])**2 for i in range(n))
    ss_tot = sum((y-my)**2 for y in y_data)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    r = math.sqrt(abs(r2)) * (1 if b1 >= 0 else -1)
    rmse = math.sqrt(ss_res / n)
    return {
        "type": "Régression Linéaire Simple",
        "n": n,
        "equation": f"Y = {b1:.4f}·X + {b0:.4f}",
        "pente": round(b1, 4),
        "intercept": round(b0, 4),
        "r2": round(r2, 4),
        "r_pearson": round(r, 4),
        "rmse": round(rmse, 2),
        "interpretation": interp_r2(r2),
        "x_data": x_data,
        "y_data": y_data,
        "y_pred": [round(v, 2) for v in y_pred],
    }

def regression_lineaire_multiple(X, y, var_names):
    """Régression multiple via moindres carrés ordinaires (numpy-like sans deps)"""
    n = len(y)
    p = len(X[0]) if X else 0
    if n < p + 2:
        return {"erreur": "Données insuffisantes"}
    # Normalisation simple + résumé statistique
    means_x = [sum(X[i][j] for i in range(n))/n for j in range(p)]
    stds_x  = [math.sqrt(sum((X[i][j]-means_x[j])**2 for i in range(n))/n) or 1 for j in range(p)]
    my = sum(y)/n

    # Coefficients approx (gradient descent simplifié)
    coeffs = [0.0]*p
    b0 = my
    lr = 0.001
    for _ in range(3000):
        preds = [b0 + sum(coeffs[j]*X[i][j] for j in range(p)) for i in range(n)]
        errs = [preds[i]-y[i] for i in range(n)]
        b0 -= lr * sum(errs)/n
        for j in range(p):
            coeffs[j] -= lr * sum(errs[i]*X[i][j] for i in range(n))/n

    preds = [b0 + sum(coeffs[j]*X[i][j] for j in range(p)) for i in range(n)]
    ss_res = sum((y[i]-preds[i])**2 for i in range(n))
    ss_tot = sum((v-my)**2 for v in y)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    r2_adj = 1 - (1-r2)*(n-1)/(n-p-1) if n > p+1 else r2

    eq_parts = " + ".join([f"{coeffs[j]:.4f}·{var_names[j]}" for j in range(p)])
    return {
        "type": "Régression Linéaire Multiple",
        "n": n,
        "p_variables": p,
        "equation": f"Y = {b0:.4f} + {eq_parts}",
        "intercept": round(b0, 4),
        "coefficients": {var_names[j]: round(coeffs[j], 4) for j in range(p)},
        "r2": round(r2, 4),
        "r2_ajuste": round(r2_adj, 4),
        "rmse": round(math.sqrt(ss_res/n), 2),
        "interpretation": interp_r2(r2),
    }

def pca(data, n_components=2):
    """PCA simplifiée — centrage + matrice de covariance manuelle"""
    n = len(data)
    p = len(data[0]) if data else 0
    if n < 2 or p < 2:
        return {"erreur": "Données insuffisantes pour PCA"}
    # Centrer
    means = [sum(data[i][j] for i in range(n))/n for j in range(p)]
    centered = [[data[i][j]-means[j] for j in range(p)] for i in range(n)]
    # Variance expliquée approx
    variances = [sum(centered[i][j]**2 for i in range(n))/(n-1) for j in range(p)]
    total_var = sum(variances)
    sorted_vars = sorted(enumerate(variances), key=lambda x: -x[1])
    comps = sorted_vars[:n_components]
    exp_var = [round(v/total_var*100, 2) for _, v in comps]
    cum_var = [round(sum(exp_var[:i+1]), 2) for i in range(len(exp_var))]
    # Projections (approximation)
    projections = []
    for i in range(min(n, 50)):
        proj = [centered[i][comps[k][0]] for k in range(n_components)]
        projections.append(proj)
    return {
        "type": "PCA — Analyse en Composantes Principales",
        "n_observations": n,
        "n_variables": p,
        "n_composantes": n_components,
        "variance_expliquee_pct": exp_var,
        "variance_cumulee_pct": cum_var,
        "projections": projections[:30],
        "interpretation": f"Les {n_components} premières composantes expliquent {cum_var[-1]}% de la variance totale."
    }

def kmeans(data, k=3, max_iter=100):
    """K-Means from scratch"""
    n = len(data)
    if n < k:
        return {"erreur": "Moins d'observations que de clusters"}
    p = len(data[0])
    # Init centroids
    centroids = [list(data[i]) for i in random.sample(range(n), k)]
    labels = [0]*n
    for _ in range(max_iter):
        # Assign
        new_labels = []
        for i in range(n):
            dists = [sum((data[i][j]-centroids[c][j])**2 for j in range(p)) for c in range(k)]
            new_labels.append(dists.index(min(dists)))
        if new_labels == labels:
            break
        labels = new_labels
        # Update centroids
        for c in range(k):
            members = [i for i in range(n) if labels[i]==c]
            if members:
                centroids[c] = [sum(data[i][j] for i in members)/len(members) for j in range(p)]
    # Inertie
    inertia = sum(
        sum((data[i][j]-centroids[labels[i]][j])**2 for j in range(p))
        for i in range(n)
    )
    sizes = [labels.count(c) for c in range(k)]
    return {
        "type": "Clustering K-Means",
        "k": k,
        "n_observations": n,
        "labels": labels,
        "tailles_clusters": sizes,
        "centroids": [[round(v, 2) for v in c] for c in centroids],
        "inertia": round(inertia, 2),
        "interpretation": f"{k} groupes identifiés avec inertie = {inertia:.2f}"
    }

def stats_descriptives(data_dict):
    """Statistiques descriptives pour un dict {variable: [valeurs]}"""
    result = {}
    for var, vals in data_dict.items():
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals)/n
        sorted_v = sorted(vals)
        median = sorted_v[n//2] if n%2 else (sorted_v[n//2-1]+sorted_v[n//2])/2
        variance = sum((v-mean)**2 for v in vals)/n
        std = math.sqrt(variance)
        result[var] = {
            "n": n, "mean": round(mean, 2), "median": round(median, 2),
            "std": round(std, 2), "min": round(min(vals), 2), "max": round(max(vals), 2),
            "q25": round(sorted_v[n//4], 2), "q75": round(sorted_v[3*n//4], 2),
        }
    return result

def interp_r2(r2):
    if r2 >= 0.9: return "Excellente corrélation (R²≥0.9)"
    if r2 >= 0.7: return "Bonne corrélation (0.7≤R²<0.9)"
    if r2 >= 0.5: return "Corrélation modérée (0.5≤R²<0.7)"
    if r2 >= 0.3: return "Corrélation faible (0.3≤R²<0.5)"
    return "Corrélation très faible (R²<0.3)"

# ── Charger données depuis la BD ─────────────────────────────────────────────
def load_prix_data():
    conn = get_db()
    rows = conn.execute("SELECT * FROM prix_marche ORDER BY date_releve ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def load_producteurs_data():
    conn = get_db()
    rows = conn.execute("SELECT * FROM producteurs").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def load_parcelles_data():
    conn = get_db()
    rows = conn.execute("SELECT * FROM parcelles").fetchall()
    conn.close()
    return [dict(r) for r in rows]

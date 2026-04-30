"""
AgriData CM — Base de données SQLite
Initialisation & Connexion
"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin de la DB (sera sur le volume)
DB_PATH = os.getenv("DB_PATH", "/app/data/agridata.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ── PRODUCTEURS ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS producteurs (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nom         TEXT NOT NULL,
        telephone   TEXT,
        localite    TEXT,
        departement TEXT,
        sexe        TEXT,
        age         INTEGER,
        taille_menage INTEGER,
        actifs_agricoles INTEGER,
        appartient_gic  INTEGER DEFAULT 0,
        nom_gic     TEXT,
        culture_principale TEXT,
        consentement_rgpd  INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now','localtime')),
        synced      INTEGER DEFAULT 0
    )""")

    # ── PARCELLES ─────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS parcelles (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        id_producteur   INTEGER REFERENCES producteurs(id) ON DELETE CASCADE,
        geojson         TEXT,          -- polygone GeoJSON
        superficie_ha   REAL,
        type_sol        TEXT,
        culture_principale TEXT,
        methode_mesure  TEXT,
        type_terrain    TEXT,
        observations    TEXT,
        created_at      TEXT DEFAULT (datetime('now','localtime')),
        synced          INTEGER DEFAULT 0
    )""")

    # ── ACTIVITES (Semis, Traitement, Récolte) ────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activites (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        id_parcelle INTEGER REFERENCES parcelles(id) ON DELETE CASCADE,
        type        TEXT,
        date_activite TEXT,
        quantite_intrants REAL,
        unite       TEXT,
        notes       TEXT,
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── PHYTOSANITAIRE ────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS phyto (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        id_parcelle INTEGER REFERENCES parcelles(id) ON DELETE CASCADE,
        organe      TEXT,
        symptome    TEXT,
        severite    TEXT,
        culture     TEXT,
        description TEXT,
        photo_path  TEXT,
        latitude    REAL,
        longitude   REAL,
        altitude    REAL,
        exif_date   TEXT,
        created_at  TEXT DEFAULT (datetime('now','localtime')),
        synced      INTEGER DEFAULT 0
    )""")

    # ── PRIX MARCHÉ ───────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prix_marche (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        marche      TEXT NOT NULL,
        date_releve TEXT NOT NULL,
        produit     TEXT NOT NULL,
        prix_fcfa   REAL,
        created_at  TEXT DEFAULT (datetime('now','localtime')),
        synced      INTEGER DEFAULT 0
    )""")

    # ── CLIMATOLOGIE ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS climatologie (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        localite        TEXT,
        mois_annee      TEXT,
        pluviometrie_mm REAL,
        jours_pluie     INTEGER,
        intensite_max   REAL,
        temp_moyenne    REAL,
        humidite_moy    REAL,
        evenement       TEXT,
        notes           TEXT,
        created_at      TEXT DEFAULT (datetime('now','localtime')),
        synced          INTEGER DEFAULT 0
    )""")

    # ── RESULTATS ANALYSES ────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        type_analyse TEXT,
        parametres  TEXT,   -- JSON
        resultats   TEXT,   -- JSON
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    )""")

    conn.commit()

    # Insérer des données de démonstration si la table est vide
    cur.execute("SELECT COUNT(*) FROM producteurs")
    if cur.fetchone()[0] == 0:
        _insert_demo_data(cur)
        conn.commit()

    conn.close()
    print("✅ Base de données initialisée")

def _insert_demo_data(cur):
    """Données de démonstration"""
    producteurs = [
        ("Jean Mbarga","237690123456","Obala","Lekié","Masculin",45,6,3,1,"SAGRIMA","Maïs",1),
        ("Marie Essama","237677234567","Mfou","Mfoundi","Féminin",38,4,2,0,"","Manioc",1),
        ("Paul Nkoa","237681345678","Mbalmayo","Nyong-et-So'o","Masculin",52,8,4,1,"CAPLAMI","Cacao",1),
        ("Victorine Atanga","237655456789","Yaoundé","Mfoundi","Féminin",29,3,1,1,"GIC-Femmes","Tomate",1),
        ("Emile Zanga","237699567890","Akonolinga","Nyong-et-Mfoumou","Masculin",41,5,3,0,"","Plantain",1),
    ]
    cur.executemany("""
        INSERT INTO producteurs (nom,telephone,localite,departement,sexe,age,
        taille_menage,actifs_agricoles,appartient_gic,nom_gic,culture_principale,consentement_rgpd)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, producteurs)

    cur.executemany("""
        INSERT INTO parcelles (id_producteur,geojson,superficie_ha,type_sol,culture_principale,methode_mesure,type_terrain)
        VALUES (?,?,?,?,?,?,?)
    """, [
        (1,'{"type":"Polygon","coordinates":[[[11.52,3.86],[11.53,3.86],[11.53,3.87],[11.52,3.87],[11.52,3.86]]]}',1.24,"Ferrallitique","Maïs","Tracé polygone GPS","Colline"),
        (2,'{"type":"Polygon","coordinates":[[[11.60,3.70],[11.61,3.70],[11.61,3.71],[11.60,3.71],[11.60,3.70]]]}',0.85,"Hydromorphe","Manioc","Tracé polygone GPS","Bas-fond"),
        (3,'{"type":"Polygon","coordinates":[[[11.50,3.80],[11.52,3.80],[11.52,3.82],[11.50,3.82],[11.50,3.80]]]}',3.12,"Ferrallitique","Cacao","Tracé polygone GPS","Plateau"),
    ])

    prix = [
        ("Mfoundi","2025-04-01","Maïs",8200),
        ("Mfoundi","2025-04-01","Cacao",22500),
        ("Mfoundi","2025-04-01","Oignon",11000),
        ("Mfoundi","2025-04-01","Manioc",6500),
        ("Sandaga","2025-04-01","Maïs",7800),
        ("Sandaga","2025-04-01","Cacao",23000),
        ("Mfoundi","2025-03-01","Maïs",7900),
        ("Mfoundi","2025-03-01","Cacao",21000),
        ("Mfoundi","2025-02-01","Maïs",7500),
        ("Mfoundi","2025-02-01","Cacao",20500),
    ]
    cur.executemany("INSERT INTO prix_marche (marche,date_releve,produit,prix_fcfa) VALUES (?,?,?,?)", prix)

    cur.executemany("""
        INSERT INTO climatologie (localite,mois_annee,pluviometrie_mm,jours_pluie,intensite_max,temp_moyenne,humidite_moy,evenement)
        VALUES (?,?,?,?,?,?,?,?)
    """, [
        ("Yaoundé","2025-04",142,18,32,24,78,"Aucun"),
        ("Yaoundé","2025-03",98,14,25,25,72,"Aucun"),
        ("Yaoundé","2025-02",45,8,18,26,65,"Sécheresse"),
        ("Yaoundé","2025-01",120,16,28,23,80,"Aucun"),
    ])

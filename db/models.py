"""
AgriData CM — Modèles Pydantic
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProducteurCreate(BaseModel):
    nom: str
    telephone: Optional[str] = None
    localite: Optional[str] = None
    departement: Optional[str] = None
    sexe: Optional[str] = None
    age: Optional[int] = None
    taille_menage: Optional[int] = None
    actifs_agricoles: Optional[int] = None
    appartient_gic: Optional[int] = 0
    nom_gic: Optional[str] = None
    culture_principale: Optional[str] = None
    consentement_rgpd: int = 0

class ParcelleCreate(BaseModel):
    id_producteur: int
    geojson: Optional[str] = None
    superficie_ha: Optional[float] = None
    type_sol: Optional[str] = None
    culture_principale: Optional[str] = None
    methode_mesure: Optional[str] = None
    type_terrain: Optional[str] = None
    observations: Optional[str] = None

class PhytoCreate(BaseModel):
    id_parcelle: Optional[int] = None
    organe: Optional[str] = None
    symptome: Optional[str] = None
    severite: Optional[str] = None
    culture: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None

class PrixMarcheCreate(BaseModel):
    marche: str
    date_releve: str
    produit: str
    prix_fcfa: float

class ClimatCreate(BaseModel):
    localite: Optional[str] = None
    mois_annee: str
    pluviometrie_mm: Optional[float] = None
    jours_pluie: Optional[int] = None
    intensite_max: Optional[float] = None
    temp_moyenne: Optional[float] = None
    humidite_moy: Optional[float] = None
    evenement: Optional[str] = None
    notes: Optional[str] = None

class AnalyseRequest(BaseModel):
    type_analyse: str  # regression_simple, regression_multiple, pca, classification_supervisee, clustering
    variable_cible: Optional[str] = None
    variables_explicatives: Optional[List[str]] = None
    dataset: Optional[str] = "prix_marche"  # quelle table utiliser
    n_clusters: Optional[int] = 3
    n_components: Optional[int] = 2

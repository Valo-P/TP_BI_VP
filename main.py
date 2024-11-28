import streamlit as st
import pandas as pd
from kpi import show_kpi
from cartes import show_cartes
import tqdm
from tqdm import tqdm
import json
from geopy.distance import geodesic
import unidecode
import os

st.sidebar.title("Valentin Poigt")
st.sidebar.subheader("M2IA - 5IABI - TP Streamlit")
st.sidebar.markdown("---")

brand_mapping = {
    "CARREFOUR": "CARREFOUR",
    "LECLERC": "LECLERC",
    "INTERMARCHE": "INTERMARCHE",
    "INTERMARCHI": "INTERMARCHE",
    "SUPER U": "SUPER U",
    "SYSTEME U": "SUPER U",
    "SYSTEM U": "SUPER U",
    "U EXPRESS": "SUPER U",
    "STATION U": "SUPER U",
    "SYSTI": "SUPER U",
    "AUCHAN": "AUCHAN",
    "CASINO": "CASINO",
    "GEANT": "CASINO",
    "ESSO": "ESSO",
    "AVIA": "AVIA",
    "NETTO": "NETTO",
    "ALDI": "ALDI",
    "G20": "G20",
    "SPAR": "SPAR",
    "8  A HUIT": "8 A HUIT",
    "ELF": "ELF",
    "ALF": "ALF",
    "AGIP": "AGIP",
    "BP": "BP",
    "DKV": "DKV",
    "ENI": "ENI",
    "ETS": "ETS",
    "JM": "JM",
    "LC": "LC",
    "LEADER-PRICE": "LEADER-PRICE",
    "AIRE": "AIRE C",
    "PROXI": "PROXI",
    "RELAIS": "RELAIS",
    "SHELL": "SHELL",
    "RENAULT": "RENAULT",
    "SIMPLY": "SIMPLY",
    "AUTRES": "AUTRES",
    "AUTRE": "AUTRES",
    "INCONNU": "INCONNU",
    "INDEPENDANT": "INDEPENDANT",
    "SANS ENSEIGNE": "INDEPENDANT",
    "PAS DE MARQUE": "INDEPENDANT",
    "SANS MARQUE": "INDEPENDANT",
}


# Regroupement des enseignes similaires
def rename_enseigne(df, search_term, new_name):
    df.loc[
        df["Enseignes"].str.contains(search_term, case=False, na=False), "Enseignes"
    ] = new_name


# Function to replace outliers with the nearest quartile value
def replace_outliers(group):
    for col in ["Gazole", "SP95", "E10", "SP98", "GPLc"]:
        if col in group:
            Q1 = group[col].quantile(0.25)
            Q3 = group[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            group[col] = group[col].apply(
                lambda x: (
                    upper_bound
                    if x > upper_bound
                    else (lower_bound if x < lower_bound else x)
                )
            )
    return group


# Charge les données en cache
@st.cache_data
def load_data():
    # Téléchargez les fichiers prix.csv et infos_stations.csv
    prix = pd.read_csv("Prix_2024.csv")
    infos_stations = pd.read_csv("Infos_Stations.csv")

    # Date
    prix["Date"] = pd.to_datetime(prix["Date"], format="%Y-%m-%d")

    # Apply the function to each station
    prix = prix.apply(replace_outliers).reset_index(drop=True)

    # Convertir latitude et longitude
    infos_stations["Latitude"] = pd.to_numeric(
        infos_stations["Latitude"], errors="coerce"
    )
    infos_stations["Longitude"] = pd.to_numeric(
        infos_stations["Longitude"], errors="coerce"
    )

    # Diviser les coordonnées en degrés (/100000)
    infos_stations["Latitude"] = infos_stations["Latitude"] / 100000
    infos_stations["Longitude"] = infos_stations["Longitude"] / 100000

    # Transformation des Enseignes
    infos_stations["Enseignes"] = infos_stations["Enseignes"].str.upper()
    infos_stations["Enseignes"] = infos_stations["Enseignes"].apply(unidecode.unidecode)

    for search_term, new_name in tqdm(brand_mapping.items(), desc="Renaming brands"):
        rename_enseigne(infos_stations, search_term, new_name)

    # FILTRE TOTAL
    infos_stations["Enseignes"] = infos_stations["Enseignes"].apply(
        lambda x: "TOTALENERGIES" if "TOTAL" in x and "TOTALENERGIES" not in x else x
    )

    # Séparez le fichier infos_stations.csv en deux fichiers
    carrefour_stations = infos_stations[infos_stations["Enseignes"] == "CARREFOUR"]
    concurrents_stations = infos_stations[infos_stations["Enseignes"] != "CARREFOUR"]

    carrefour_stations.to_csv("Carrefour.csv", index=False)
    concurrents_stations.to_csv("Concurrents.csv", index=False)

    # Identifiez les concurrents dans un rayon de 10 km pour chaque station Carrefour
    carrefour_stations = carrefour_stations.to_dict("records")
    concurrents_stations = concurrents_stations.to_dict("records")

    if not os.path.exists("carrefour_concurrents.json"):
        carrefour_concurrents = {}

        for carrefour in tqdm(carrefour_stations, desc="Processing Carrefour stations"):
            carrefour_location = (carrefour["Latitude"], carrefour["Longitude"])
            carrefour_concurrents[carrefour["id"]] = []

            for concurrent in concurrents_stations:
                concurrent_location = (concurrent["Latitude"], concurrent["Longitude"])
                distance = geodesic(carrefour_location, concurrent_location).km

                if distance <= 10:
                    carrefour_concurrents[carrefour["id"]].append(concurrent["id"])

        with open("carrefour_concurrents.json", "w") as f:
            json.dump(carrefour_concurrents, f)

    return prix, infos_stations


# Charge les données
prix, infos_stations = load_data()

# Crée un menu de navigation et paramètres
st.sidebar.title("Navigation")

# Ajoute les pages
page = st.sidebar.radio(
    "Choisissez une page",
    ["Étape A : KPI", "Étape B : Cartes"],
)

# Sélection de la plage de dates
min_date = prix["Date"].min().date()
max_date = prix["Date"].max().date()
date_range = st.sidebar.date_input(
    "Sélectionnez une plage de dates",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

# Affiche le contenu de la page sélectionnée
if len(date_range) == 2:
    if date_range[0] and date_range[1] and date_range[0] < date_range[1]:
        if page == "Étape A : KPI":
            show_kpi(prix, infos_stations, date_range)
        elif page == "Étape B : Cartes":
            show_cartes(prix, infos_stations, date_range)
    else:
        st.warning("Veuillez sélectionner une plage de dates valide.")
else:
    st.warning("Veuillez sélectionner une plage de dates valide.")

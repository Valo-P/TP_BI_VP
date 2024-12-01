import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def set_sidebar(min_date, max_date):
    # Sidebar - Paramètres de la date - Multi-Select de Jours
    date = st.sidebar.selectbox(
        "Sélectionnez une date",
        options=pd.date_range(min_date, max_date).strftime("%Y-%m-%d"),
    )

    return date


def show_kpi(prix, infos_stations, min_date, max_date):
    st.title("Page KPI")

    # Sidebar
    date = set_sidebar(min_date, max_date)

    # Filtrer les enseignes d'intérêt
    enseignes_interet = [
        "CARREFOUR",
        "AUCHAN",
        "LECLERC",
        "TOTALENERGIES ACCESS",
        "TOTALENERGIES",
        "INTERMARCHE",
        "SUPER U",
    ]
    infos_stations_filtered = infos_stations[
        infos_stations["Enseignes"].isin(enseignes_interet)
    ]

    # Filtrer les données de prix par la plage de dates sélectionnée
    if date:
        prix = prix[prix["Date"] == date]

    # Fusionner les données de prix et d'infos stations
    merged_data = pd.merge(prix, infos_stations_filtered, left_on="id", right_on="id")

    # Calculer le prix moyen par jour pour chaque enseigne
    product_columns = ["Gazole", "SP95", "E10", "SP98", "GPLc"]

    # Supprimer les lignes contenant des valeurs None ou <= 0 dans les colonnes de produits
    merged_data = merged_data.dropna(subset=product_columns)
    for col in product_columns:
        merged_data = merged_data[merged_data[col] > 0]

    prix_moyen_par_enseigne = (
        merged_data.groupby(["Date", "Enseignes"])[product_columns].mean().reset_index()
    ).round(3)

    st.markdown("---")

    # Afficher les KPI sous forme de colonnes (1 colonne par enseigne, 1 ligne par KPI)
    st.subheader("Prix moyen par enseigne")

    # Créer des colonnes pour chaque enseigne
    enseignes = prix_moyen_par_enseigne["Enseignes"].unique()
    cols = st.columns(len(enseignes))

    for i, enseigne in enumerate(enseignes):
        with cols[i]:
            st.write(enseigne)
            enseigne_data = prix_moyen_par_enseigne[
                prix_moyen_par_enseigne["Enseignes"] == enseigne
            ]
            for carburant in product_columns:
                if carburant in enseigne_data.columns:
                    mean_value = enseigne_data[carburant].mean()
                    st.metric(label=carburant, value=f"{mean_value:.3f}")

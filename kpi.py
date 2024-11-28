import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def show_kpi(prix, infos_stations, date_range):
    st.title("Page KPI")

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
    if date_range:
        start_date, end_date = date_range
        prix = prix[
            (prix["Date"] >= pd.to_datetime(start_date))
            & (prix["Date"] <= pd.to_datetime(end_date))
        ]

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

    # Afficher les KPI sous forme de graphiques
    for carburant in ["Gazole", "SP95", "E10", "SP98", "GPLc"]:
        if carburant in prix.columns:
            fig = px.line(
                prix_moyen_par_enseigne,
                x="Date",
                y=carburant,
                color="Enseignes",
                title=f"Prix moyen du {carburant} par enseigne",
                labels={"Date": "Date", carburant: "Prix moyen (€)"},
            )
            st.plotly_chart(fig, use_container_width=True)

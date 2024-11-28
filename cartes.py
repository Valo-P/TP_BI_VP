import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import json
import plotly.express as px


def show_cartes(prix, infos_stations):
    st.title("Page Cartes")

    # Charger les données des stations Carrefour et des concurrents
    carrefour_stations = pd.read_csv("Carrefour.csv")
    concurrents_stations = pd.read_csv("Concurrents.csv")

    # Charger les données des concurrents dans un rayon de 10 km à partir du fichier JSON
    with open("carrefour_concurrents.json", "r") as f:
        carrefour_concurrents = json.load(f)

    # Sélectionner une station Carrefour
    carrefour_ids = carrefour_stations["id"].tolist()
    selected_carrefour_id = st.selectbox(
        "Sélectionnez une station Carrefour", carrefour_ids
    )

    st.markdown("---")

    st.subheader("Affichage sur une carte")

    # Créer une carte centrée sur la station Carrefour sélectionnée
    selected_carrefour = carrefour_stations[
        carrefour_stations["id"] == selected_carrefour_id
    ].iloc[0]
    m = folium.Map(
        location=[selected_carrefour["Latitude"], selected_carrefour["Longitude"]],
        zoom_start=12,
    )

    # Ajouter la station Carrefour sélectionnée à la carte
    folium.Marker(
        location=[selected_carrefour["Latitude"], selected_carrefour["Longitude"]],
        popup=f"{selected_carrefour['Enseignes']} - {selected_carrefour['Ville']}",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    # Ajouter les stations concurrentes dans un rayon de 10 km à la carte
    for concurrent_id in carrefour_concurrents[str(selected_carrefour_id)]:
        concurrent = concurrents_stations[
            concurrents_stations["id"] == concurrent_id
        ].iloc[0]
        folium.Marker(
            location=[concurrent["Latitude"], concurrent["Longitude"]],
            popup=f"{concurrent['Enseignes']} - {concurrent['Ville']}",
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)

    # Afficher la carte dans Streamlit
    folium_static(m)

    st.markdown("---")

    st.subheader("Tableau de comparaison des prix")

    # Afficher les prix des carburants dans un tableau
    carburants = ["SP95", "SP98", "Gazole", "E85", "GPLc"]
    prix_carrefour = prix[prix["id"] == selected_carrefour_id]

    # Créer un DataFrame pour stocker les prix
    prix_comparaison = pd.DataFrame(
        columns=["Station", "Enseigne", "Ville"] + carburants
    )

    # Ajouter les prix de la station Carrefour sélectionnée
    prix_carrefour_data = pd.DataFrame(
        [
            {
                "Station": selected_carrefour_id,
                "Enseigne": selected_carrefour["Enseignes"],
                "Ville": selected_carrefour["Ville"],
                **{
                    carburant: round(prix_carrefour[carburant].values[0], 3)
                    for carburant in carburants
                },
            }
        ]
    )

    # Ajouter les prix des stations concurrentes
    concurrents_data = []
    for concurrent_id in carrefour_concurrents[str(selected_carrefour_id)]:
        prix_concurrent = prix[prix["id"] == concurrent_id]
        concurrent = concurrents_stations[concurrents_stations["id"] == concurrent_id]
        if not concurrent.empty and not prix_concurrent.empty:
            concurrent = concurrent.iloc[0]
            concurrents_data.append(
                {
                    "Station": concurrent_id,
                    "Enseigne": concurrent["Enseignes"],
                    "Ville": concurrent["Ville"],
                    **{
                        carburant: round(prix_concurrent[carburant].values[0], 3)
                        for carburant in carburants
                    },
                }
            )

    prix_concurrents_df = pd.DataFrame(concurrents_data)

    # Concaténer les données de Carrefour et des concurrents
    prix_comparaison = pd.concat(
        [prix_carrefour_data, prix_concurrents_df], ignore_index=True
    )

    # Trier les prix par ordre décroissant pour chaque type de carburant
    for carburant in carburants:
        prix_comparaison = prix_comparaison.sort_values(by=carburant, ascending=False)

    # Afficher le tableau dans Streamlit
    st.dataframe(
        prix_comparaison.style.apply(
            lambda x: [
                (
                    "background-color: green"
                    if x["Station"] == selected_carrefour_id
                    else ""
                )
                for _ in x
            ],
            axis=1,
        )
    )

    st.markdown("---")

    st.subheader("Graphique de comparaison des prix")

    # Pour chaque type de carburant, affichez une courbe montrant l’évolution des prix
    # pour la station Carrefour sélectionnée ainsi que celle de ses concurrents dans un
    # rayon de 10 km.

    for carburant in carburants:
        filtered_prix = prix[
            (
                prix["id"].isin(
                    [selected_carrefour_id]
                    + carrefour_concurrents[str(selected_carrefour_id)]
                )
            )
            & (prix[carburant] > 0)
        ]
        filtered_prix = filtered_prix.merge(
            pd.concat([carrefour_stations, concurrents_stations])[["id", "Enseignes"]],
            on="id",
            how="left",
        )
        fig = px.line(
            filtered_prix,
            x="Date",
            y=carburant,
            color="Enseignes",
            title=f"Prix du {carburant} pour la station Carrefour et ses concurrents",
            labels={"Date": "Date", carburant: "Prix (€)"},
        )
        st.plotly_chart(fig, use_container_width=True)


# Fonction pour afficher la carte Folium dans Streamlit
def folium_static(m, width=700, height=500):
    from streamlit_folium import st_folium

    st_folium(m, width=width, height=height)

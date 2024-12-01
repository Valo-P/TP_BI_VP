import pandas as pd
import math


def haversine(lat1, lon1, lat2, lon2):
    # Convertir les degrés en radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # Rayon moyen de la Terre en kilomètres
    R = 6371.0
    # Différences de coordonnées
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # Formule de Haversine
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Distance en kilomètres
    distance = R * c
    return distance


def list_concurrents(id, D1, D2):
    L_conc = list()
    for x in D1:
        d = haversine(D2[id][0], D2[id][1], D1[x][0], D1[x][1])
        # d = great_circle(D2[id], D1[x]).kilometers
        if d <= 10:
            L_conc.append(x)
    return L_conc

import sqlite3
import requests
import pandas as pd
from datetime import datetime

# 1. Requisição das fontes
STATUS_URL = "https://api.cyclocity.fr/contracts/ljubljana/gbfs/v3/station_status.json"
INFO_URL = "https://api.cyclocity.fr/contracts/ljubljana/gbfs/v3/station_information.json"

status_raw = requests.get(STATUS_URL).json()["data"]["stations"]
info_raw = requests.get(INFO_URL).json()["data"]["stations"]

# 2. Tratamento dos dados cadastrais (Info)
stations_info = []
for station in info_raw:
    # Trata a lista de nomes extraindo o texto do primeiro idioma disponível
    nome_limpo = station["name"][0]["text"] if isinstance(station.get("name"), list) and station["name"] else "Desconhecido"
    
    stations_info.append({
        "station_id": str(station["station_id"]),
        "name": nome_limpo,
        "address": station.get("address", ""),
        "capacity": int(station.get("capacity", 0)),
        "lat": station.get("lat"),
        "lon": station.get("lon")
    })

df_info = pd.DataFrame(stations_info)

# 3. Tratamento dos dados dinâmicos (Status)
stations_status = []
for station in status_raw:
    stations_status.append({
        "station_id": str(station["station_id"]),
        "bikes_available": int(station.get("num_vehicles_available", 0)),
        "docks_available": int(station.get("num_docks_available", 0)),
        "is_renting": int(station.get("is_renting", False)),
        "is_returning": int(station.get("is_returning", False)),
        "last_reported": station.get("last_reported")
    })

df_status = pd.DataFrame(stations_status)

# 4. Cruzamento dos dados (JOIN relacional)
df_merged = pd.merge(df_info, df_status, on="station_id", how="inner")

# 5. Métricas operacionais derivadas
# Evita divisão por zero caso alguma estação venha com capacidade zerada
df_merged["occupancy_rate"] = (
    df_merged["bikes_available"] / df_merged["capacity"].replace(0, 1)
).round(2)

# Carimbo de data/hora da ingestão
df_merged["ingested_at"] = datetime.utcnow().isoformat()

# Visualização de validação no terminal
print("Total de estações processadas:", len(df_merged))
print("\n--- PRIMEIRAS 5 ESTAÇÕES (Tabela Limpa) ---")
print(df_merged[["station_id", "name", "capacity", "bikes_available", "docks_available", "occupancy_rate"]].head())

# 6. Conexão e persistência no banco SQLite
conn = sqlite3.connect("bicikelj.db")

# Salva o DataFrame como tabela relacional. 
# 'append' permite acumular snapshots ao longo do tempo para análises temporais.
df_merged.to_sql("station_snapshots", conn, if_exists="append", index=False)

conn.close()
print("\n[OK] Dados persistidos com sucesso na tabela 'station_snapshots' em 'bicikelj.db'!")
import sqlite3
import pandas as pd

# Conecta ao banco gerado
conn = sqlite3.connect("bicikelj.db")

# Escreva a sua query SQL dentro das aspas triplas
query = """
WITH doadoras AS (
    SELECT 
        station_id AS id_origem,
        name AS estacao_origem,
        bikes_available AS bikes_sobrando,
        lat AS lat_origem,
        lon AS lon_origem
    FROM station_snapshots
    WHERE docks_available <= 1 AND bikes_available >= 10
),
recebedoras AS (
    SELECT 
        station_id AS id_destino,
        name AS estacao_destino,
        capacity - bikes_available AS vagas_livres,
        lat AS lat_destino,
        lon AS lon_destino
    FROM station_snapshots
    WHERE bikes_available = 0
),
matriz_rotas AS (
    SELECT 
        d.estacao_origem,
        d.bikes_sobrando,
        r.estacao_destino,
        r.vagas_livres,
        -- Cálculo de distância aproximada em KM para Liubliana
        ROUND(
            SQRT(
                ( (d.lat_origem - r.lat_destino) * 111.0 ) * ( (d.lat_origem - r.lat_destino) * 111.0 ) +
                ( (d.lon_origem - r.lon_destino) * 77.0 ) * ( (d.lon_origem - r.lon_destino) * 77.0 )
            ), 2
        ) AS distancia_km,
        -- Ranqueia as estações recebedoras da mais próxima para a mais distante
        ROW_NUMBER() OVER (
            PARTITION BY d.estacao_origem 
            ORDER BY (
                ( (d.lat_origem - r.lat_destino) * 111.0 ) * ( (d.lat_origem - r.lat_destino) * 111.0 ) +
                ( (d.lon_origem - r.lon_destino) * 77.0 ) * ( (d.lon_origem - r.lon_destino) * 77.0 )
            ) ASC
        ) AS prioridade_rota
    FROM doadoras d
    CROSS JOIN recebedoras r
)
SELECT 
    estacao_origem,
    bikes_sobrando,
    estacao_destino,
    vagas_livres,
    distancia_km
FROM matriz_rotas
WHERE prioridade_rota = 1
ORDER BY distancia_km ASC;
"""

# Executa a query e exibe formatada via DataFrame
df_result = pd.read_sql_query(query, conn)
print(df_result)

conn.close()
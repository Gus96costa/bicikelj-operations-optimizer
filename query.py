import sqlite3
import pandas as pd

# Conecta ao banco gerado
conn = sqlite3.connect("bicikelj.db")

# Escreva a sua query SQL dentro das aspas triplas
query = """
SELECT 
    CASE 
        WHEN bikes_available = 0 THEN '1. RUPTURA TOTAL (Sem Bicicletas)'
        WHEN bikes_available BETWEEN 1 AND 2 THEN '2. ALERTA CRÍTICO (Estoque Baixo)'
        WHEN docks_available = 0 THEN '3. BLOQUEIO TOTAL (Sem Vagas)'
        WHEN docks_available BETWEEN 1 AND 2 THEN '4. ALERTA SOBRECARGA (Poucas Vagas)'
        ELSE '5. OPERAÇÃO REGULAR'
    END AS status_operacional,
    COUNT(*) AS total_estacoes,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM station_snapshots), 1) AS percentual_rede
FROM station_snapshots
GROUP BY status_operacional
ORDER BY status_operacional ASC;
"""

# Executa a query e exibe formatada via DataFrame
df_result = pd.read_sql_query(query, conn)
print(df_result)

conn.close()
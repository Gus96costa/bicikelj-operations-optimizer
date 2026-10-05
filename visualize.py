import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Configurar estética visual
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'Arial', 'font.size': 11})

conn = sqlite3.connect("bicikelj.db")

# 2. Query 1: Distribuição do Status da Rede
query_kpi = """
SELECT 
    CASE 
        WHEN bikes_available = 0 THEN 'Ruptura (Sem Bikes)'
        WHEN bikes_available BETWEEN 1 AND 2 THEN 'Alerta Crítico'
        WHEN docks_available = 0 THEN 'Bloqueio (Sem Vagas)'
        WHEN docks_available BETWEEN 1 AND 2 THEN 'Alerta Sobrecarga'
        ELSE 'Operação Regular'
    END AS status,
    COUNT(*) AS total
FROM station_snapshots
GROUP BY status
ORDER BY total DESC;
"""
df_kpi = pd.read_sql_query(query_kpi, conn)

# 3. Query 2: Top 7 Estações com Menor Oferta
query_critical = """
SELECT name, bikes_available, capacity
FROM station_snapshots
ORDER BY bikes_available ASC, capacity DESC
LIMIT 7;
"""
df_critical = pd.read_sql_query(query_critical, conn)
conn.close()

# 4. Construção da Figura com 2 Subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Gráfico 1: Barras horizontais de status da malha
cores_kpi = ['#2ecc71' if 'Regular' in s else '#e74c3c' if 'Ruptura' in s or 'Bloqueio' in s else '#f39c12' for s in df_kpi['status']]
sns.barplot(data=df_kpi, y='status', x='total', palette=cores_kpi, ax=ax1)
ax1.set_title("Diagnóstico de Saúde da Rede (Snapshot Atual)", fontsize=14, weight='bold', pad=15)
ax1.set_xlabel("Número de Estações")
ax1.set_ylabel("")

# Adiciona rótulos numéricos nas barras
for p in ax1.patches:
    ax1.annotate(f"{int(p.get_width())}", (p.get_width() + 0.8, p.get_y() + 0.5), va='center')

# Gráfico 2: Terminais Críticos com Risco de Ruptura
sns.barplot(data=df_critical, y='name', x='bikes_available', color='#e74c3c', ax=ax2)
ax2.set_title("Top Estações em Ruptura Imediata", fontsize=14, weight='bold', pad=15)
ax2.set_xlabel("Bicicletas Disponíveis")
ax2.set_ylabel("")

plt.tight_layout()

# 5. Exportar a imagem gerada
os.makedirs("assets", exist_ok=True)
caminho_imagem = "assets/network_health.png"
plt.savefig(caminho_imagem, dpi=300, bbox_inches='tight')
plt.close()

print(f"[OK] Gráficos gerados com sucesso e guardados em: {caminho_imagem}")
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# 1. Configuração estética executiva
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Helvetica Neue', 'Arial', 'sans-serif'],
    'axes.edgecolor': '#E2E8F0',
    'axes.linewidth': 0.8,
    'figure.facecolor': '#F8FAFC',
    'axes.facecolor': '#FFFFFF'
})

conn = sqlite3.connect("bicikelj.db")

# -------------------------------------------------------------
# 2. Consultas Analíticas (Cobrindo os casos do estudo)
# -------------------------------------------------------------

# CASO 1: Classificação Operacional da Malha
q_kpi = """
SELECT 
    CASE 
        WHEN bikes_available = 0 THEN 'Ruptura (0 Bikes)'
        WHEN bikes_available BETWEEN 1 AND 2 THEN 'Alerta Défice (1-2)'
        WHEN docks_available = 0 THEN 'Bloqueio (0 Vagas)'
        WHEN docks_available BETWEEN 1 AND 2 THEN 'Alerta Sobrecarga'
        ELSE 'Operação Regular'
    END AS status,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM station_snapshots), 1) AS pct
FROM station_snapshots
GROUP BY status
ORDER BY total DESC;
"""
df_kpi = pd.read_sql_query(q_kpi, conn)

# CASO 2: Comparativo dos Extremos (Top Bloqueios vs Top Rupturas)
q_extremes = """
SELECT name, bikes_available, capacity, 'Ruptura' AS tipo
FROM station_snapshots
WHERE bikes_available = 0
ORDER BY capacity DESC
LIMIT 5;
"""
q_full = """
SELECT name, bikes_available, capacity, 'Bloqueio' AS tipo
FROM station_snapshots
WHERE docks_available = 0
ORDER BY capacity DESC
LIMIT 5;
"""
df_extremes = pd.concat([pd.read_sql_query(q_extremes, conn), pd.read_sql_query(q_full, conn)])

# CASO 3: As Melhores Rotas de Rebalanceamento (CTEs + Window Functions)
q_routes = """
WITH doadoras AS (
    SELECT station_id, name, bikes_available, lat, lon
    FROM station_snapshots
    WHERE docks_available <= 1 AND bikes_available >= 10
),
recebedoras AS (
    SELECT station_id, name, capacity - bikes_available AS vagas, lat, lon
    FROM station_snapshots
    WHERE bikes_available = 0
),
rotas AS (
    SELECT 
        d.name AS origem,
        r.name AS destino,
        ROUND(
            SQRT(
                ((d.lat - r.lat) * 111.0) * ((d.lat - r.lat) * 111.0) +
                ((d.lon - r.lon) * 77.0) * ((d.lon - r.lon) * 77.0)
            ), 2
        ) AS distancia_km,
        ROW_NUMBER() OVER (
            PARTITION BY d.name 
            ORDER BY (
                ((d.lat - r.lat) * 111.0) * ((d.lat - r.lat) * 111.0) +
                ((d.lon - r.lon) * 77.0) * ((d.lon - r.lon) * 77.0)
            ) ASC
        ) AS ranking
    FROM doadoras d
    CROSS JOIN recebedoras r
)
SELECT origem || ' ➔ ' || destino AS rota, distancia_km
FROM rotas
WHERE ranking = 1
ORDER BY distancia_km ASC
LIMIT 6;
"""
df_routes = pd.read_sql_query(q_routes, conn)

# CASO 4: Dados Geográficos com Status para Mapa
q_geo = """
SELECT 
    name, lat, lon, bikes_available, docks_available, capacity,
    CASE 
        WHEN bikes_available = 0 THEN 'Ruptura (Sem Bikes)'
        WHEN docks_available = 0 THEN 'Bloqueio (Sem Vagas)'
        ELSE 'Regular / Alerta Leve'
    END AS status_geo
FROM station_snapshots;
"""
df_geo = pd.read_sql_query(q_geo, conn)
conn.close()

# -------------------------------------------------------------
# 3. Construção do Dashboard Executivo (Grid 2x2)
# -------------------------------------------------------------
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
fig.patch.set_facecolor('#F8FAFC')

# --- QUADRANTE 1: Diagnóstico de Saúde da Malha ---
cores_kpi = {
    'Operação Regular': '#10B981',
    'Ruptura (0 Bikes)': '#EF4444',
    'Alerta Défice (1-2)': '#F97316',
    'Bloqueio (0 Vagas)': '#8B5CF6',
    'Alerta Sobrecarga': '#3B82F6'
}
barras1 = ax1.barh(df_kpi['status'], df_kpi['total'], color=[cores_kpi.get(s, '#94A3B8') for s in df_kpi['status']], height=0.55, zorder=3)
ax1.set_title("1. Distribuição Operacional da Rede (88 Estações)", fontsize=11, weight='bold', color='#0F172A', loc='left', pad=10)
ax1.set_xlabel("Volume de Estações", fontsize=9, color='#64748B')
ax1.set_xlim(0, max(df_kpi['total']) * 1.25)
ax1.invert_yaxis()
for bar, pct in zip(barras1, df_kpi['pct']):
    w = bar.get_width()
    ax1.text(w + 0.8, bar.get_y() + bar.get_height()/2, f"{int(w)} ({pct}%)", va='center', fontsize=8.5, weight='bold', color='#334155')

# --- QUADRANTE 2: Extremos Operacionais (Ruptura vs Bloqueio) ---
cores_ext = ['#EF4444' if t == 'Ruptura' else '#8B5CF6' for t in df_extremes['tipo']]
nomes_formatados = [f"[{t.upper()}] {n[:22]}..." if len(n) > 22 else f"[{t.upper()}] {n}" for n, t in zip(df_extremes['name'], df_extremes['tipo'])]
ax2.barh(nomes_formatados, df_extremes['capacity'], color='#E2E8F0', height=0.55, label='Capacidade Doca', zorder=2)
ax2.barh(nomes_formatados, df_extremes['bikes_available'], color=cores_ext, height=0.55, label='Bikes Presentes', zorder=3)
ax2.set_title("2. Extremos Críticos: Défice Total vs. Saturação Máxima", fontsize=11, weight='bold', color='#0F172A', loc='left', pad=10)
ax2.set_xlabel("Capacidade vs. Veículos", fontsize=9, color='#64748B')
ax2.invert_yaxis()
ax2.legend(loc='lower right', fontsize=8.5, frameon=True, facecolor='#FFFFFF')

# --- QUADRANTE 3: Rotas de Rebalanceamento Otimizadas ---
rotas_invertidas = df_routes.iloc[::-1]
barras3 = ax3.barh(rotas_invertidas['rota'], rotas_invertidas['distancia_km'], color='#0284C7', height=0.5, zorder=3)
ax3.set_title("3. Logística de Rebalanceamento: Menor Trajeto (Origem ➔ Destino)", fontsize=11, weight='bold', color='#0F172A', loc='left', pad=10)
ax3.set_xlabel("Distância de Deslocamento da Van (km)", fontsize=9, color='#64748B')
ax3.set_xlim(0, max(df_routes['distancia_km']) * 1.3)
for bar in barras3:
    w = bar.get_width()
    ax3.text(w + 0.05, bar.get_y() + bar.get_height()/2, f"{w:.2f} km", va='center', fontsize=8.5, weight='bold', color='#0369A1')

# --- QUADRANTE 4: Dispersão Geográfica Real (Mapa de Liubliana) ---
cores_mapa = {'Ruptura (Sem Bikes)': '#EF4444', 'Bloqueio (Sem Vagas)': '#8B5CF6', 'Regular / Alerta Leve': '#CBD5E1'}
for status_tipo, cor in cores_mapa.items():
    subset = df_geo[df_geo['status_geo'] == status_tipo]
    size = 75 if status_tipo != 'Regular / Alerta Leve' else 35
    alpha = 0.95 if status_tipo != 'Regular / Alerta Leve' else 0.45
    ax4.scatter(subset['lon'], subset['lat'], c=cor, s=size, alpha=alpha, edgecolors='none', label=status_tipo, zorder=3)

ax4.set_title("4. Malha Espacial de Liubliana: Zonas de Ruptura e Bloqueio", fontsize=11, weight='bold', color='#0F172A', loc='left', pad=10)
ax4.set_xlabel("Longitude", fontsize=9, color='#64748B')
ax4.set_ylabel("Latitude", fontsize=9, color='#64748B')
ax4.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='#FFFFFF')

# Estilização limpa para todos os eixos
for ax in [ax1, ax2, ax3, ax4]:
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.grid(True, linestyle='--', alpha=0.5, color='#F1F5F9', zorder=1)
    ax.tick_params(colors='#475569', labelsize=8.5)

# Título Corporativo Unificado
plt.suptitle("BICIKELJ OPERATIONAL INTELLIGENCE DASHBOARD", fontsize=15, weight='bold', color='#0F172A', x=0.06, y=0.98, ha='left')
plt.figtext(0.06, 0.955, "Auditoria de Telemetria GBFS v3 | Modelagem Relacional & Algoritmo de Roteamento Logístico", fontsize=9.5, color='#64748B', ha='left')

plt.subplots_adjust(top=0.92, hspace=0.32, wspace=0.28, left=0.06, right=0.96, bottom=0.06)

# -------------------------------------------------------------
# 4. Gravação da Imagem em Alta Resolução
# -------------------------------------------------------------
os.makedirs("assets", exist_ok=True)
caminho = "assets/network_health.png"
plt.savefig(caminho, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
plt.close()

print(f"[OK] Dashboard operacional completo gerado com sucesso em: {caminho}")
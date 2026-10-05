import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Configuração tipográfica e estética limpa
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Helvetica Neue', 'Arial', 'sans-serif'],
    'axes.edgecolor': '#CBD5E1',
    'axes.linewidth': 0.8,
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF'
})

conn = sqlite3.connect("bicikelj.db")

# 2. Query 1: Diagnóstico da Malha (KPIs)
query_kpi = """
SELECT 
    CASE 
        WHEN bikes_available = 0 THEN 'Ruptura Total (Sem Veículos)'
        WHEN bikes_available BETWEEN 1 AND 2 THEN 'Alerta Crítico (Défice Iminente)'
        WHEN docks_available = 0 THEN 'Bloqueio Total (Sem Vagas)'
        WHEN docks_available BETWEEN 1 AND 2 THEN 'Alerta Sobrecarga'
        ELSE 'Operação Regular'
    END AS status,
    COUNT(*) AS total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM station_snapshots), 1) AS percentual
FROM station_snapshots
GROUP BY status
ORDER BY total DESC;
"""
df_kpi = pd.read_sql_query(query_kpi, conn)

# 3. Query 2: Terminais em Ruptura Imediata
query_critical = """
SELECT name, bikes_available, capacity
FROM station_snapshots
ORDER BY bikes_available ASC, capacity DESC
LIMIT 8;
"""
df_critical = pd.read_sql_query(query_critical, conn)
conn.close()

# 4. Mapeamento de Cores Corporativas
palette_map = {
    'Operação Regular': '#059669',                  # Emerald
    'Ruptura Total (Sem Veículos)': '#DC2626',      # Crimson
    'Alerta Crítico (Défice Iminente)': '#EA580C',  # Amber
    'Bloqueio Total (Sem Vagas)': '#7C3AED',        # Violet
    'Alerta Sobrecarga': '#2563EB'                 # Blue
}
df_kpi['cor'] = df_kpi['status'].map(lambda s: palette_map.get(s, '#64748B'))

# 5. Construção da Figura
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.2), gridspec_kw={'width_ratios': [1.1, 1]})

# --- GRÁFICO 1: Distribuição da Malha ---
bars1 = ax1.barh(df_kpi['status'], df_kpi['total'], color=df_kpi['cor'], height=0.55, zorder=3)
ax1.set_title("Classificação Operacional da Malha (88 Estações)", fontsize=12, weight='bold', color='#0F172A', loc='left', pad=12)
ax1.set_xlabel("Número de Estações", fontsize=9.5, color='#64748B', labelpad=8)
ax1.set_xlim(0, max(df_kpi['total']) * 1.25)
ax1.tick_params(axis='y', labelsize=9.5, colors='#1E293B')
ax1.tick_params(axis='x', labelsize=9, colors='#64748B')
ax1.invert_yaxis()

for bar, pct in zip(bars1, df_kpi['percentual']):
    width = bar.get_width()
    y_pos = bar.get_y() + bar.get_height() / 2
    ax1.text(width + 1.2, y_pos, f"{int(width)} ({pct}%)", va='center', ha='left', fontsize=9, weight='bold', color='#334155')

# --- GRÁFICO 2: Terminais Críticos (Disponibilidade vs Capacidade) ---
ax2.barh(df_critical['name'], df_critical['capacity'], color='#F1F5F9', edgecolor='#E2E8F0', height=0.55, label='Capacidade Total', zorder=2)
ax2.barh(df_critical['name'], df_critical['bikes_available'], color='#EF4444', height=0.55, label='Bicicletas Disponíveis', zorder=3)

ax2.set_title("Terminais Críticos: Disponibilidade vs. Capacidade", fontsize=12, weight='bold', color='#0F172A', loc='left', pad=12)
ax2.set_xlabel("Volume de Bicicletas / Vagas", fontsize=9.5, color='#64748B', labelpad=8)
ax2.tick_params(axis='y', labelsize=9, colors='#1E293B')
ax2.tick_params(axis='x', labelsize=9, colors='#64748B')
ax2.set_xlim(0, max(df_critical['capacity']) * 1.22)
ax2.invert_yaxis()
ax2.legend(loc='lower right', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=8.5)

for i, row in df_critical.reset_index().iterrows():
    ax2.text(row['capacity'] + 0.6, i, f"{row['bikes_available']}/{row['capacity']} vagas", va='center', ha='left', fontsize=8.5, color='#64748B', weight='500')

# Limpeza de bordas e grelha
for ax in [ax1, ax2]:
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.xaxis.grid(True, linestyle='--', alpha=0.6, color='#E2E8F0', zorder=1)
    ax.yaxis.grid(False)

# Título Principal e Subtítulo Executivo
plt.suptitle("BicikeLJ Telemetry Audit: Network Health & Critical Stockouts", fontsize=15, weight='bold', color='#0F172A', x=0.06, y=1.03, ha='left')
plt.figtext(0.06, 0.98, "Auditoria operacional em tempo real via GBFS v3 | Ljubljana, Eslovénia", fontsize=9.5, color='#64748B', ha='left')

plt.tight_layout()

# 6. Gravação
os.makedirs("assets", exist_ok=True)
caminho = "assets/network_health.png"
plt.savefig(caminho, dpi=300, bbox_inches='tight')
plt.close()

print(f"[OK] Dashboard executivo gerado com sucesso em: {caminho}")
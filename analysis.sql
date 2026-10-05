-- ================================================================
-- PROJETO: BicikeLJ Operations Optimizer (Ljubljana)
-- OBJETIVO: Auditoria de Risco Operacional e Ruptura de Serviço
-- ================================================================

-- 1. Diagnóstico Geral da Rede (KPI Executivo)
-- Agrupa a malha em faixas de risco para dimensionar o atrito total
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


-- 2. Lista Prioritária para Reabastecimento (Falta de Veículos)
-- Identifica as estações com maior déficit de oferta
SELECT 
    station_id,
    name,
    capacity,
    bikes_available,
    docks_available,
    occupancy_rate
FROM station_snapshots
WHERE bikes_available < 3
ORDER BY bikes_available ASC, capacity DESC;


-- 3. Lista Prioritária para Alívio de Carga (Risco de Bloqueio de Devolução)
-- Identifica estações saturadas que exigem retirada urgente de bicicletas
SELECT 
    station_id,
    name,
    capacity,
    bikes_available,
    docks_available,
    occupancy_rate
FROM station_snapshots
WHERE docks_available < 3
ORDER BY docks_available ASC, capacity DESC;

-- 4. Matriz de Rebalanceamento Logístico (Pareamento Origem -> Destino)
-- Identifica a estação vazia mais próxima para cada estação com sobrecarga de oferta
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
        ROUND(
            SQRT(
                ( (d.lat_origem - r.lat_destino) * 111.0 ) * ( (d.lat_origem - r.lat_destino) * 111.0 ) +
                ( (d.lon_origem - r.lon_destino) * 77.0 ) * ( (d.lon_origem - r.lon_destino) * 77.0 )
            ), 2
        ) AS distancia_km,
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
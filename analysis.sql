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
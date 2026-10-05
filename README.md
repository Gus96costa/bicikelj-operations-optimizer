# BicikeLJ Fleet & Operations Optimizer

An end-to-end operational analytics pipeline designed to audit real-time service disruptions, station capacity bottlenecks, and logistical rebalancing routes across the BicikeLJ bike-sharing network in Ljubljana, Slovenia.

---

## 1. Executive Summary

Urban bike-sharing systems face recurring supply-demand imbalances during peak hours. In pedestrianized city centers and transit corridors, stations experience severe stockouts (empty docks) or return deadlocks (full docks). 

Using real-time telemetry from Ljubljana's General Bikeshare Feed Specification (GBFS v3) API, this project models station telemetry into a relational database and executes SQL-driven operational auditing. 

### Key Findings:
- **43.2% Network Friction:** Only 56.8% of stations operate within balanced occupancy thresholds.
- **Stockout Severity:** 29.6% of the network (26 stations) suffers from acute vehicle shortages, with 14.8% experiencing total service rupture (`bikes_available = 0`).
- **Return Bottlenecks:** Major commercial and transit hubs (e.g., Prešernov Trg, Supernova Rudnik) hit 100% capacity, blocking user returns.
- **Logistical Feasibility:** Over 60% of critical empty stations can be serviced by donor stations within a **< 2.5 km radius**, drastically reducing redistribution fuel costs and van travel times.

---

## 2. System Architecture

```text
GBFS v3 API (Ljubljana)
   │
   ├──> station_information.json (Metadata, capacity, coordinates)
   └──> station_status.json      (Real-time vehicle & dock telemetry)
           │
           ▼
     Python (extract.py)
     ├── Data parsing & JSON localization handling
     ├── Data integrity validation & occupancy calculations
     └── Automated load to SQLite (bicikelj.db)
           │
           ▼
     SQL Engine (analysis.sql)
     ├── Network Health KPI aggregation (CASE WHEN, GROUP BY)
     ├── Supply/demand priority auditing
     └── Logistical route matching (CTEs, CROSS JOIN, Window Functions)


3. Tech Stack
Data Ingestion & Transformation: Python 3.13, Pandas, Requests.

Database & Querying: SQLite3, ANSI SQL (Common Table Expressions, Window Functions, Haversine/Euclidean geo-distance).

Version Control: Git, GitHub.

Data Source: OPSI - Open Data Slovenia / Cyclocity GBFS Feed.

4. Key Analytical Queries
A. Network Health Matrix (KPI Classification)
Categorizes all 88 active stations into operational health tiers to give leadership an immediate health score of the entire urban grid.

B. Proximity-Based Logistical PairingSolves the redistribution vehicle routing problem by matching saturated donor stations (docks_available <= 1) with the nearest empty recipient stations (bikes_available = 0) using Euclidean distance calibrated for Ljubljana coordinates:

| Donor Station (Overload) | Available Bikes | Receiver Station (Zero Stock) | Free Docks | Transit Distance |
| :--- | :--- | :--- | :--- | :--- |
| **Zaloška C. - Grablovičeva C.** | 16 | Savsko Naselje 1 - Šmartinska C. | 20 | **0.99 km** |
| **IKEA** | 20 | Savsko Naselje 1 - Šmartinska C. | 20 | **1.11 km** |
| **Povšetova - Grablovičeva** | 19 | Savsko Naselje 1 - Šmartinska C. | 20 | **1.27 km** |
| **Živalski Vrt** | 19 | Koseški Bajer | 20 | **1.78 km** |
| **Tržaška C. - Ilirija** | 19 | P+R Barje | 20 | **2.15 km** |
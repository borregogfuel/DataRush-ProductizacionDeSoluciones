# Late Night Safety Index (NYC Taxi) — Equipo "las_tortugas_cosmicales"

This folder contains a small backend + frontend to analyze NYC Yellow Taxi late-night solo rides and visualize a simple Safety Activity Index per pickup zone.

## Quick start

### Backend (Flask + Pandas)
1. Open a terminal:
```powershell
Set-Location 'C:\Users\guill\DataRush-ProductizacionDeSoluciones\solucion-las_tortugas_cosmicales\backend'
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
```
3. Run the server:
```powershell
python app.py
```
- It loads Jan 2023 data directly from AWS, filters late-night solo rides (00:00–03:59, passenger_count=1),
  computes per-zone stats, and exposes endpoints:
  - `GET /summary`
  - `GET /zone-stats`
  - `GET /hourly-trends`
  - `GET /preview`

### Frontend (static HTML)
1. Open:
```
C:\Users\guill\DataRush-ProductizacionDeSoluciones\solucion-las_tortugas_cosmicales\frontend\index.html
```
2. Ensure the API input shows `http://127.0.0.1:5000`, then click "Reload".

## Notes
- CORS is enabled in the backend (`flask-cors`).
- `zone_stats.csv` is generated locally for convenience and is gitignored.
- To change the month, point `URL` in `backend/app.py` to another parquet (e.g., `yellow_tripdata_2023-02.parquet`).

## Tech
- Python (pandas, flask, flask-cors, pyarrow)
- Frontend: HTML + Chart.js


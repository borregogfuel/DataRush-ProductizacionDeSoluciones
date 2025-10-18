# NYC Taxi ML Models - AVG FARE & SAFETY INDEX

Este repositorio contiene la versión finalizada del proyecto de productización: modelos, código backend, frontend y artefactos de despliegue.

Última actualización: entrega final fusionada en `main` (incluye datos de ejemplo y guía de despliegue).

Enlaces rápidos
- GitHub Pages (frontend público): https://borregogfuel.github.io/DataRush-ProductizacionDeSoluciones/
- Video final (entrega): https://drive.google.com/drive/folders/184xXN4EKyNklBfooxUAnJOPT8vzCevBh?usp=sharing

Resumen de componentes añadidos
- Frontend: `solucion-las_tortugas_cosmicales/frontend/map.html` (deployable via GitHub Pages)
- Backend/Production: `production/api/app.py`, scripts en `production/scripts/` y `production/Dockerfile`
- Data de ejemplo y mapeos: `solucion-las_tortugas_cosmicales/ML/`
- Documentación de despliegue: `DEPLOYMENT_GUIDE_SECURE.md`, `EC2_DEPLOYMENT_GUIDE.md`

Instalación rápida

```powershell
pip install -r requirements.txt
```

Configuración (rutas importantes)

```yaml
data:
  parquet_path: "solucion-las_tortugas_cosmicales/ML/parquet_data"
  location_mapping: "solucion-las_tortugas_cosmicales/ML/LocationID_to_pretinct.csv"
  crime_data: "solucion-las_tortugas_cosmicales/ML/crime_data/NYPD_Complaint_Data_Historic_20251015.csv"
```

Uso rápido

- Ejecutar backend de producción (local):
  - Construir imagen Docker (desde `production/`):
    ```powershell
    cd production
    docker build -t datarush-production .
    docker run -p 8000:8000 datarush-production
    ```
- Ejecutar frontend local (abrir `solucion-las_tortugas_cosmicales/frontend/map.html` en navegador)
- Ejecutar pruebas:
  ```powershell
  python -m pytest
  ```

Entrega y notas importantes

- Se ha añadido un CSV histórico de incidentes (`NYPD_Complaint_Data_Historic_20251015.csv`) como datos de muestra para reproducibilidad. Estos archivos son grandes — si necesitas que los quite del repo para reducir tamaño, dímelo y lo gestionamos con herramienta de historial (`git-filter-repo` o BFG).
- Se creó `aaVideoFinal/videofinal.txt` con el enlace al material final.

Contacto y entrega

Si quieres que prepare un tag o release para la entrega final, puedo crear `v1.0` y pushearlo ahora.

---

## Estructura del Proyecto (técnico)

```
├── README.md
├── requirements.txt
├── config.yaml
├── solucion-las_tortugas_cosmicales/
│   ├── frontend/
│   │   └── map.html
│   ├── backend/
│   │   └── app.py
│   └── ML/
│       ├── parquet_data/
│       └── LocationID_to_pretinct.csv
├── production/
│   ├── api/
│   │   └── app.py
│   ├── Dockerfile
│   └── scripts/
└── docs/
```

## Notas técnicas

- Modelos: LightGBM con split temporal. Parámetros y rutas en `config.yaml`.
- Para reproducir entrenamientos usar los scripts en `solucion-las_tortugas_cosmicales/` o `production/ml_engine/`.

Si quieres que empuje este cambio a `main` ahora (commit + push), lo hago y creo un tag `v1.0` si lo confirmas.
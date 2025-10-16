NYC Taxi Zones GeoJSON

The interactive map (map.html) needs the NYC Taxi Zones geometry. It tries sources in order:

1. ArcGIS REST GeoJSON (recommended):
   https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Taxi_Zones/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson

2. NYC Open Data geospatial export:
   https://data.cityofnewyork.us/api/geospatial/755u-8jsi?method=export&format=GeoJSON

3. Local fallback file: taxi_zones.geojson (same folder as this README)

If online sources are blocked, download a local copy:

PowerShell:
  Invoke-WebRequest -Uri "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/NYC_Taxi_Zones/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson" -OutFile "taxi_zones.geojson"

Then open map.html and it will use the local file if online fetch fails.

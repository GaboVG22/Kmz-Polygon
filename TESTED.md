# Pruebas realizadas

Aplicación V5 estable validada antes de entregar.

## Pruebas ejecutadas correctamente

- Compilación de `core.py`
- Compilación de `app.py`
- Lectura de 3 archivos KMZ de ejemplo
- Conversión de coordenadas WGS84 a CRS proyectado
- Cálculo de áreas y perímetros
- Interpolación con 2 capas por intervalo
- Cálculo de volúmenes por tramo
- Curva cota-volumen
- Generación de PNG 3D
- Generación de PNG cota-área
- Generación de PNG cota-volumen
- Generación de KML consolidado
- Generación de KMZ consolidado
- Generación de GeoJSON

## Resultado de prueba

- Capas base: 3
- Capas interpoladas: 4
- Tramos de volumen: 6
- CRS cálculo: EPSG:32719
- Volumen total de prueba: 13,496,213.27 m³

## Nota

En este entorno visible no está instalado el módulo `streamlit`, pero el archivo `requirements.txt`
lo incluye para ejecución local, GitHub o Streamlit Cloud.

Para probar rápidamente:
1. Ejecute `pip install -r requirements.txt`
2. Ejecute `streamlit run app.py`
3. Active `Usar KMZ de ejemplo incluidos`
4. Presione `Generar modelo`

# KMZ 3D Volúmenes — GitHub executable edition

Aplicación para cargar múltiples archivos KMZ, asignar cotas, visualizar capas en 3D, interpolar capas y calcular volúmenes.

## Formas de uso

### Opción A — Ejecutar localmente con Python

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Opción B — Generar ejecutable Windows desde GitHub

Este repositorio incluye GitHub Actions para crear un `.exe`.

Archivo principal del workflow:

```text
.github/workflows/build-windows-exe.yml
```

Pasos:

1. Subir esta carpeta a GitHub.
2. Ir a **Actions**.
3. Ejecutar **Build Windows executable**.
4. Descargar el artefacto `KMZ_3D_Volumenes_Windows`.
5. Descomprimir y abrir `KMZ_3D_Volumenes.exe`.

Ver instrucciones completas en:

```text
GITHUB_EJECUTABLE.md
```

## Prueba rápida dentro de la app

Una vez abierta la aplicación, active:

```text
Usar KMZ de ejemplo incluidos
```

Luego presione:

```text
Generar modelo
```

## Archivos importantes

- `app.py`: aplicación Streamlit.
- `core.py`: lógica geométrica y cálculo volumétrico.
- `streamlit_launcher.py`: lanzador para empaquetar como `.exe`.
- `.github/workflows/build-windows-exe.yml`: construye el ejecutable en GitHub.
- `sample_data/`: KMZ de ejemplo.

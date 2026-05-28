# Validación local

Se validó localmente:

- Sintaxis de `app.py`.
- Sintaxis de `core.py`.
- Sintaxis de `streamlit_launcher.py`.
- Existencia del workflow `.github/workflows/build-windows-exe.yml`.
- Existencia del workflow `.github/workflows/release-windows-exe.yml`.

La construcción real del `.exe` debe ejecutarse en GitHub Actions, porque se necesita un runner Windows con PyInstaller.

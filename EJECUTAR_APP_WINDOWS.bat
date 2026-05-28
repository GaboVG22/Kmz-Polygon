@echo off
title KMZ 3D Volumenes V5
echo ============================================
echo KMZ 3D Volumenes V5 - Instalacion y ejecucion
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en PATH.
    echo Instale Python 3.11 desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Creando entorno virtual...
python -m venv .venv

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Iniciando aplicacion Streamlit...
echo Cuando abra el navegador, active "Usar KMZ de ejemplo incluidos" para probar.
echo.
streamlit run app.py

pause

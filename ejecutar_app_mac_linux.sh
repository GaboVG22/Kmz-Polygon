#!/usr/bin/env bash
set -e

echo "============================================"
echo "KMZ 3D Volumenes V5 - Instalacion y ejecucion"
echo "============================================"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Iniciando aplicacion Streamlit..."
echo "Cuando abra el navegador, active 'Usar KMZ de ejemplo incluidos' para probar."
streamlit run app.py

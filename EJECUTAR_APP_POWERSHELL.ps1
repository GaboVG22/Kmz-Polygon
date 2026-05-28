Write-Host "============================================"
Write-Host "KMZ 3D Volumenes V5 - Instalacion y ejecucion"
Write-Host "============================================"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python no esta instalado o no esta en PATH."
    Write-Host "Instale Python 3.11 desde https://www.python.org/downloads/"
    Read-Host "Presione Enter para salir"
    exit 1
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host ""
Write-Host "Iniciando aplicacion Streamlit..."
Write-Host "Cuando abra el navegador, active 'Usar KMZ de ejemplo incluidos' para probar."
streamlit run app.py

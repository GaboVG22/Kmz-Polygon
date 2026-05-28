# IMPORTANTE: estás viendo el README, no la aplicación

Si al abrir ves una página como esta:

```text
KMZ 3D Volúmenes V5 estable
Ejecutar
pip install -r requirements.txt
streamlit run app.py
```

entonces **NO estás dentro de la aplicación**.  
Estás viendo el archivo `README.md` del repositorio.

La aplicación real es `app.py` y debe ejecutarse con Streamlit.

---

# Forma más simple en Windows

1. Descargue y descomprima el ZIP.
2. Entre a la carpeta.
3. Haga doble clic en:

```text
EJECUTAR_APP_WINDOWS.bat
```

4. Espere que instale las dependencias.
5. Se abrirá una página en el navegador.
6. Active:

```text
Usar KMZ de ejemplo incluidos
```

7. Presione:

```text
Generar modelo
```

---

# Forma manual

Abra una terminal dentro de la carpeta de la aplicación y ejecute:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

En Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

---

# En GitHub

GitHub solo muestra los archivos del repositorio.  
**GitHub no ejecuta directamente aplicaciones Streamlit.**

Para verla como aplicación web debe desplegarse en:

```text
https://streamlit.io/cloud
```

Configuración:

```text
Repository: tu repositorio
Branch: main
Main file path: app.py
```

---

# Prueba rápida

La aplicación trae KMZ de ejemplo.

Cuando abra la aplicación real, en la barra lateral marque:

```text
Usar KMZ de ejemplo incluidos
```

Luego haga clic en:

```text
Generar modelo
```

Si aparece la vista 3D, la aplicación está funcionando correctamente.

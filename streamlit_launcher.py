"""
Lanzador de escritorio para la aplicación Streamlit.

Este archivo permite empaquetar la app con PyInstaller.
Al abrir el .exe, levanta un servidor local de Streamlit y abre el navegador.
"""

import os
import socket
import sys
import tempfile
import threading
import webbrowser
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """Devuelve una ruta válida tanto en desarrollo como dentro de PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return str(Path(base_path) / relative_path)


def find_available_port(preferred: int = 8501) -> int:
    """Usa el puerto preferido si está libre; si no, busca uno disponible."""
    for port in [preferred, 8502, 8503, 8504, 8505]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    app_path = resource_path("app.py")
    port = find_available_port(8501)
    url = f"http://127.0.0.1:{port}"

    print("Iniciando KMZ 3D Volúmenes...")
    print(f"Aplicación: {app_path}")
    print(f"URL local: {url}")

    threading.Timer(2.5, lambda: webbrowser.open(url)).start()

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.headless=true",
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--global.developmentMode=false",
    ]

    from streamlit.web import cli as stcli

    sys.exit(stcli.main())


if __name__ == "__main__":
    main()

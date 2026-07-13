"""Ejecuta las comprobaciones del proyecto desde un solo comando."""

import subprocess
import sys
from pathlib import Path


RAIZ = Path(__file__).parent
COMPROBACIONES = [
    "check_streamlit.py",
    "check_pca.py",
    "check_lambda.py",
    "check_ec2.py",
    "check_etl.py",
    "check_scraper.py",
]


def main():
    archivos = list(COMPROBACIONES)

    if "--api" in sys.argv:
        archivos.append("check_api.py")

    for archivo in archivos:
        print(f"\nEjecutando {archivo}...")
        resultado = subprocess.run([sys.executable, str(RAIZ / archivo)])
        if resultado.returncode != 0:
            return resultado.returncode

    print("\nProyecto: todas las comprobaciones han terminado correctamente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

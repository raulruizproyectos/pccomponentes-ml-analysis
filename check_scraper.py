"""Comprueba la configuración del contenedor y el temporizador."""

from pathlib import Path


RAIZ = Path(__file__).parent

dockerfile = (RAIZ / "Dockerfile.scraper").read_text(encoding="utf-8")
servicio = (RAIZ / "deploy/pccomponentes-scraper.service").read_text(
    encoding="utf-8"
)
temporizador = (RAIZ / "deploy/pccomponentes-scraper.timer").read_text(
    encoding="utf-8"
)

assert "python:3.11-slim" in dockerfile
assert "ejecutar_scraping_programado.py" in dockerfile
assert "docker run --rm" in servicio
assert "OnCalendar=Sun" in temporizador

print("Scraper: contenedor y programacion correctos")

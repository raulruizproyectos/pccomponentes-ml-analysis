"""Comprueba los endpoints principales con FastAPI ya iniciado."""

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen

from dotenv import load_dotenv


load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://13.61.42.45:8000").rstrip("/")

PRUEBAS = (
    ("/health", None),
    ("/db/health", None),
    ("/consulta", {"limit": 2}),
    ("/modelos", None),
    ("/modelos/clustering", None),
    ("/modelos/sentimiento", None),
    ("/graficas/resumen", None),
    ("/graficas/precios", None),
    ("/graficas/valoraciones", None),
    ("/sentiment", {"producto_id": "ram_0012"}),
    ("/similar-products", {"producto_id": "ram_0012", "limit": 5}),
    (
        "/ask",
        {
            "producto_id": "ram_0012",
            "pregunta": "Que opinan los usuarios",
        },
    ),
    ("/modelos/pca", {"categoria": "memoria_ram"}),
    ("/modelos/pca", {"categoria": "tarjeta_grafica"}),
)


def crear_url(ruta, parametros):
    if not parametros:
        return f"{API_BASE_URL}{ruta}"
    return f"{API_BASE_URL}{ruta}?{urlencode(parametros)}"


def main():
    errores = 0

    for ruta, parametros in PRUEBAS:
        url = crear_url(ruta, parametros)
        try:
            with urlopen(url, timeout=30) as respuesta:
                json.load(respuesta)
                assert respuesta.status == 200
            print(f"OK    {url}")
        except Exception as error:
            errores += 1
            print(f"ERROR {url}: {error}")

    if errores:
        print(f"API: {errores} comprobacion(es) fallida(s)")
        return 1

    print("API: comprobacion completa correcta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

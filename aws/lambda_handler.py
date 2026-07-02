"""
Handler de AWS Lambda activado por eventos S3.

Flujo (Fase 01 del enunciado):
    1. El scraping sube JSON a S3 (brutos/ o procesados/) por categoría.
    2. Lambda recibe el evento y descarga los ficheros necesarios.
    3. Si llegan datos brutos, ejecuta la limpieza de la categoría.
    4. Carga los datos procesados en PostgreSQL (RDS).

Categorías soportadas:
    - ram
    - tarjetas_graficas

Punto de entrada para Lambda:
    aws.lambda_handler.handler
"""

from __future__ import annotations

import os

from aws.orquestador import procesar_objeto_s3
from aws.paths import parsear_registro_evento_s3


def _database_url() -> str:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise ValueError("DATABASE_URL no configurada en el entorno de Lambda.")
    return database_url


def handler(event: dict, context) -> dict:
    database_url = _database_url()
    resultados = []

    for registro in event.get("Records", []):
        objeto = parsear_registro_evento_s3(registro)
        resultados.append(
            procesar_objeto_s3(objeto.bucket, objeto.clave, database_url)
        )

    return {
        "procesados": len(resultados),
        "resultados": resultados,
    }
"""Scraping semanal pequeño de RAM y subida de los datos brutos a S3."""

import os

from aws.categorias import obtener_categoria
from aws.s3_client import ClienteS3
from scrapers.detalle_ram import ejecutar_detalle
from scrapers.listado_ram import ejecutar_listado


def main():
    paginas = int(os.getenv("SCRAPER_PAGINAS", "1"))
    productos = int(os.getenv("SCRAPER_PRODUCTOS", "5"))
    delay = float(os.getenv("SCRAPER_DELAY", "4"))

    ejecutar_listado(
        paginas=paginas,
        productos_por_pagina=productos,
    )
    ejecutar_detalle(
        desde_cero=True,
        delay_segundos=delay,
    )

    subidos = ClienteS3().subir_brutos(obtener_categoria("ram"))
    print(f"Scraping terminado: {len(subidos)} archivos subidos a S3")


if __name__ == "__main__":
    main()

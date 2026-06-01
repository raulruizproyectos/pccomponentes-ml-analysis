# pccomponentes-ml-analysis

Proyecto colaborativo enfocado en la extracción, procesamiento y análisis de datos de la página web de PCcomponentes. El objetivo es construir un pipeline completo de datos que permita obtener información desde fuentes web, limpiarla, almacenarla, analizar tendencias, generar visualizaciones y desarrollar modelos de Machine Learning para mostrar los resultados mediante una aplicación web interactiva.


## Descripcion

El proyecto empieza con la extraccion de informacion de memorias RAM y tarjetas graficas. Mas adelante se ampliara segun el enunciado definitivo.

## Objetivo

Organizar el repositorio para que el equipo pueda trabajar de forma clara en la primera fase del proyecto: buscar fuentes de datos y preparar el scraping inicial.

## Integrantes

- Dani
- Raul
- Andres

## Estructura del repositorio

```text
pccomponentes-ml-analysis/
|-- README.md
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- To_Do_List
|-- enunciado.ipynb
|-- run_scraper.py
|-- config/
|   `-- settings.py
|-- scrapers/
|   |-- ram_category.py
|   |-- ram_product_detail.py
|   |-- gpu_category.py
|   |-- gpu_product_detail.py
|   `-- utils.py
|-- data/
|   `-- raw/
|       |-- ram/
|       `-- tarjetas_graficas/
|-- pipeline/
|   `-- etl_processor.py
|-- models/
|-- api/
|-- streamlit_app/
|-- colaboradores/
|   |-- dani/
|   |-- raul/
|   `-- andres/
|-- comun/
|   |-- datos/
|   |   |-- brutos/
|   |   `-- procesados/
|   `-- codigo/
|       `-- extraccion/
|-- notebooks/
|   |-- 01_eda_ram.ipynb
|   `-- 02_eda_tarjetas_graficas.ipynb
|-- docs/
|   `-- fuentes_tarjetas_graficas.md
```

## Lineas de extraccion iniciales

El proyecto se divide en dos familias de productos:

- RAM: extraccion de listados, detalles tecnicos, precios y resenas.
- Tarjetas graficas: extraccion de modelo, precio, VRAM, GPU, bus de memoria, reloj boost, salidas de video, resolucion maxima, resenas y valoraciones.

Los datos crudos se guardaran como JSON dentro de `data/raw/`. No se deben subir datos reales al repositorio.

## Tareas iniciales

1. Buscar fuentes de datos para memorias RAM.
2. Buscar fuentes de datos para tarjetas graficas.
3. Definir que campos se van a extraer.
4. Preparar los primeros scripts de extraccion.
5. Guardar los datos obtenidos en `comun/datos/brutos/`.

## Estado actual

Estructura inicial simplificada. Todavia no hay scraping implementado ni datos guardados.

## Recomendaciones para GitHub

- Usar `colaboradores/` para pruebas o avances individuales.
- Pasar a `comun/` solo lo que el equipo decida conservar.
- Hacer commits pequeños y claros.
- No subir datos pesados al repositorio.

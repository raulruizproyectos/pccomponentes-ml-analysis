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
|-- configuracion.local
|-- .gitignore
|-- To_Do_List
|-- enunciado.md
|-- ejecutar_scraper.py
|-- database/
|   |-- conexion.py
|   |-- consultas.py
|   `-- inserciones.py
|-- config/
|   `-- settings.py
|-- scrapers/
|   |-- listado.py
|   |-- detalle.py
|   `-- utilidades.py
|-- data/
|   `-- brutos/
|       |-- ram/
|       `-- tarjetas_graficas/
|-- pipeline/
|   `-- etl_processor.py
|-- models/
|-- api/
|-- streamlit_app/
|-- comun/
|   |-- datos/
|   |   |-- brutos/
|   |   `-- procesados/
|   `-- codigo/
|       `-- extraccion/
|-- notebooks/
|   |-- 01_eda_ram.ipynb
|   |-- 02_eda_tarjetas_graficas.ipynb
|   |-- 03_conexion_postgresql.ipynb
|   `-- 04_validacion_database.ipynb
|-- docs/
|   `-- fuentes_tarjetas_graficas.md
```

## Lineas de extraccion iniciales

El proyecto se divide en dos familias de productos:

- RAM: extraccion de listados, detalles tecnicos, precios y resenas.
- Tarjetas graficas: extraccion de modelo, precio, VRAM, GPU, bus de memoria, reloj boost, salidas de video, resolucion maxima, resenas y valoraciones.

Los datos brutos se guardan como JSON dentro de `comun/datos/brutos/`.

**Nota del equipo:** Se ha decidido incluir los archivos de datos reales (listado_ram.json y detalle_ram.json) en el repositorio bajo `comun/datos/brutos/`. Esto es para facilitar el trabajo colaborativo interno entre los compañeros del proyecto (no es un repo público). Si en el futuro se hace público o se amplía el equipo, se revisará esta decisión.

## Tareas iniciales

1. Buscar fuentes de datos para memorias RAM.
2. Buscar fuentes de datos para tarjetas graficas.
3. Definir que campos se van a extraer.
4. Preparar los primeros scripts de extraccion.
5. Guardar los datos obtenidos en `comun/datos/brutos/`.

## Estado actual

- Scraper de listado + detalle para **memorias RAM** completado (1646 productos).
- Extracción de resenas (muestra embebida en JSON-LD, hasta 15 por producto) + especificaciones técnicas (tipo, capacidad, kit, frecuencia, CL, compat etc) implementada y probada.
- Datos brutos en comun/datos/brutos/ram/ (detalle_ram.json enriquecido offline con specs; para resenas completas hace falta re-run del detalle o fetch selectivo).
- DB schema e inserciones extendidas para RAM (productos + especificaciones_ram + resenas).
- Pendiente: ETL de carga a PostgreSQL, EDA en notebooks, inicio de scraper de tarjetas gráficas.


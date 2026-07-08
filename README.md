# PCComponentes ML Analysis

Proyecto para recoger, limpiar, guardar y analizar datos de componentes de PCComponentes.

Trabajamos con memorias RAM y tarjetas graficas. Los datos se limpian, se guardan en PostgreSQL y se utilizan para analisis exploratorio, clustering y analisis de sentimiento.

## Integrantes

- Dani
- Raul
- Andres

## Flujo del proyecto

1. Extraer datos de PcComponentes.
2. Guardar los datos brutos en JSON.
3. Limpiar y adaptar los datos.
4. Cargar los datos limpios en PostgreSQL.
5. Analizar los datos con notebooks.
6. Generar modelos y resultados.
7. Guardar los resultados de modelos en PostgreSQL.
8. Consumir los datos desde FastAPI y Streamlit.

## Estado actual

### RAM

Completado:

- Extraccion de productos, especificaciones y resenas.
- Limpieza de datos.
- Carga en PostgreSQL.
- EDA de datos brutos y limpios.
- Clustering con K-Means.
- Guardado de clustering en PostgreSQL.
- Analisis de sentimiento con Hugging Face.
- Guardado de sentimiento en PostgreSQL.

Conteos actuales:

- Productos: 1646.
- Especificaciones: 1574.
- Distribuciones de valoraciones: 1574.
- Resenas: 5876.
- Resultados de sentimiento: 5876.

Tablas principales:

- `productos`
- `especificaciones_ram`
- `distribucion_valoraciones`
- `resenas`
- `resultados_clustering_ram`
- `resultados_sentimiento`

### GPU

Completado:

- Incorporacion del JSON de GPU preprocesado por IA.
- Limpieza y adaptacion al esquema del proyecto.
- Generacion de archivos procesados.
- Carga en PostgreSQL.
- Extraccion y carga de resenas GPU.
- Clustering con K-Means.
- Guardado de clustering en PostgreSQL.
- Analisis de sentimiento con Hugging Face.
- Guardado de sentimiento en PostgreSQL.

Conteos actuales:

- Productos: 500.
- Especificaciones: 500.
- Distribuciones de valoraciones: 500.
- Resenas GPU: 3564.
- Resultados de clustering: 500.
- Resultados de sentimiento: 3564.

Tablas principales:

- `productos`
- `especificaciones_gpu`
- `distribucion_valoraciones`
- `resenas_gpu`
- `resultados_clustering_gpu`
- `resultados_sentimiento_gpu`

Grupos de clustering GPU:

- `alta_gama`: 137 productos.
- `gama_media`: 198 productos.
- `ficha_incompleta`: 165 productos.

Las resenas GPU se guardan en `resenas_gpu` porque no incluyen valoracion individual por resena.

## Estructura principal

```text
pccomponentes-ml-analysis/
|-- api/
|-- aws/
|-- comun/
|-- config/
|-- data/
|   |-- brutos/
|   `-- procesados/
|-- database/
|-- docs/
|-- models/
|-- notebooks/
|   |-- 01_eda_ram.ipynb
|   |-- 02_eda_tarjetas_graficas.ipynb
|   |-- 03_conexion_postgresql.ipynb
|   |-- 04_eda_ram_datos_limpios.ipynb
|   |-- 05_preparacion_modelo_ram.ipynb
|   |-- 06_nlp_resenas_ram.ipynb
|   |-- 07_sentimiento_resenas_ram.ipynb
|   |-- 08_preparacion_modelo_gpu.ipynb
|   |-- 09_sentimiento_resenas_gpu.ipynb
|   |-- base_de_datos_tgraf.ipynb
|   |-- limpieza_tgraf.ipynb
|   `-- scraping_tgraf.ipynb
|-- pipeline/
|-- scrapers/
|-- streamlit_app/
|-- ejecutar_aws.py
|-- ejecutar_scraper.py
|-- requirements.txt
`-- README.md
```

## Notebooks

### 01_eda_ram.ipynb

Analisis inicial de los datos brutos de RAM.

### 02_eda_tarjetas_graficas.ipynb

Analisis inicial de tarjetas graficas.

### 03_conexion_postgresql.ipynb

Pruebas de conexion con PostgreSQL.

### 04_eda_ram_datos_limpios.ipynb

Analisis de datos limpios de RAM desde PostgreSQL.

### 05_preparacion_modelo_ram.ipynb

Preparacion de datos y clustering de RAM.

### 06_nlp_resenas_ram.ipynb

Analisis exploratorio de resenas RAM.

### 07_sentimiento_resenas_ram.ipynb

Analisis de sentimiento de resenas RAM y guardado en PostgreSQL.

### 08_preparacion_modelo_gpu.ipynb

Preparacion de datos y clustering de tarjetas graficas.

### 09_sentimiento_resenas_gpu.ipynb

Analisis de sentimiento de resenas GPU y guardado en PostgreSQL.

### Notebooks GPU auxiliares

Estos notebooks proceden del trabajo previo de GPU y se conservan por trazabilidad:

- `base_de_datos_tgraf.ipynb`
- `limpieza_tgraf.ipynb`
- `scraping_tgraf.ipynb`

## Base de datos

El esquema principal esta en:

```text
database/esquema.sql
```

Archivos de insercion:

- `database/inserciones_ram.py`
- `database/inserciones_gpu.py`

Tablas principales:

- `productos`
- `especificaciones_ram`
- `especificaciones_gpu`
- `distribucion_valoraciones`
- `resenas`
- `resenas_gpu`
- `resultados_clustering_ram`
- `resultados_clustering_gpu`
- `resultados_sentimiento`
- `resultados_sentimiento_gpu`

## Pipeline

Limpieza RAM:

```powershell
python -B pipeline/limpieza_ram.py
```

Carga RAM a PostgreSQL:

```text
pipeline/carga_ram_postgresql.py
```

Limpieza GPU:

```powershell
python -B pipeline/limpieza_gpu.py
```

Carga GPU a PostgreSQL:

```text
pipeline/carga_gpu_postgresql.py
```

## Modelos

### Clustering

RAM y GPU usan K-Means para agrupar productos segun variables numericas y categoricas preparadas.

Los resultados se guardan en PostgreSQL para no ejecutar el modelo en cada consulta.

Tablas:

- `resultados_clustering_ram`
- `resultados_clustering_gpu`

### Sentimiento

Modelo utilizado:

```text
nlptown/bert-base-multilingual-uncased-sentiment
```

Tablas:

- `resultados_sentimiento`
- `resultados_sentimiento_gpu`

## AWS

La carpeta `aws/` contiene la estructura para trabajar con S3, RDS y Lambda.

Archivos relevantes:

- `aws/categorias.py`
- `aws/infra_rds.py`
- `aws/infra_s3.py`
- `aws/lambda_handler.py`
- `aws/orquestador.py`
- `aws/s3_client.py`

Pendiente:

- Validar RDS.
- Validar S3.
- Controlar ejecucion de Lambda.
- Ejecutar cargas reales solo con autorizacion.

## FastAPI

La carpeta `api/` esta preparada, pero la API todavia no esta desarrollada.

FastAPI debera consultar PostgreSQL y exponer endpoints para:

- Estado del servicio.
- Productos.
- Especificaciones.
- Clustering RAM/GPU.
- Sentimiento RAM/GPU.
- Datos agregados para graficas.
- Recomendacion mediante filtros y ranking SQL.

## Streamlit

La carpeta `streamlit_app/` esta preparada, pero la app todavia no esta desarrollada.

Streamlit debera consumir FastAPI, no conectarse directamente a PostgreSQL.

Vistas recomendadas:

- Resumen general.
- Filtros de productos.
- Comparativas RAM/GPU.
- Graficas de clustering.
- Graficas de sentimiento.
- Tabla de productos recomendados.
- Ficha de producto.

## Instalacion

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Dependencias principales:

- `pandas`
- `psycopg[binary]`
- `matplotlib`
- `seaborn`
- `scikit-learn`
- `joblib`
- `boto3`
- `torch`
- `transformers`

FastAPI, Uvicorn y Streamlit se anadiran cuando se desarrolle esa parte.

## Proximos pasos

1. Revisar la estructura existente de `api/`.
2. Crear FastAPI y conectar con PostgreSQL.
3. Crear endpoints para productos, clustering y sentimiento.
4. Crear Streamlit consumiendo FastAPI.
5. Validar AWS/RDS/S3/Lambda.
6. Preparar revision final y presentacion.

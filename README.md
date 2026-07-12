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

AWS no forma parte del MVP local actual. El proyecto funciona en local con PostgreSQL y FastAPI.

Tambien se ha probado la conexion de FastAPI contra AWS RDS. RDS contiene las tablas del proyecto y los resultados de modelos.

Archivos relevantes:

- `aws/categorias.py`
- `aws/infra_rds.py`
- `aws/infra_s3.py`
- `aws/lambda_handler.py`
- `aws/orquestador.py`
- `aws/s3_client.py`

Pendiente:

- Validar RDS/S3/Lambda solo si se decide continuar con la parte cloud.
- Ejecutar cargas reales en AWS solo con autorizacion.

## FastAPI

La carpeta `api/` contiene una primera API funcional con FastAPI.

La API consulta PostgreSQL con `psycopg` y expone endpoints para:

- Estado del servicio.
- Estado de la conexion con PostgreSQL.
- Consulta de productos con filtros y ordenacion.
- Resumen de modelos.
- Clustering RAM/GPU.
- Sentimiento RAM/GPU.
- Datos agregados para graficas.
- Ranking basico de productos mediante filtros SQL.

Endpoints actuales:

- `GET /health`
- `GET /db/health`
- `GET /consulta`
- `GET /modelos`
- `GET /modelos/clustering`
- `GET /modelos/sentimiento`
- `GET /graficas/resumen`
- `GET /graficas/precios`
- `GET /graficas/valoraciones`

Parametros principales de `/consulta`:

- `categoria`: `memoria_ram` o `tarjeta_grafica`.
- `marca`: filtra por marca exacta.
- `precio_min`: precio minimo.
- `precio_max`: precio maximo.
- `orden`: `precio`, `valoracion` u `opiniones`.
- `limit`: numero de productos devueltos, entre 1 y 50.

Ejemplo:

```text
http://127.0.0.1:8000/consulta?categoria=tarjeta_grafica&marca=MSI&precio_max=500&orden=valoracion&limit=5
```

Ejecutar la API:

```powershell
python -m uvicorn api.main:app --reload
```

La API puede consultar PostgreSQL local o AWS RDS cambiando `DATABASE_URL` en `.env`.

## Streamlit

La aplicacion esta en `streamlit_app/streamlit_main.py`.

Streamlit consume los datos desde FastAPI y no se conecta directamente a PostgreSQL.

La aplicacion tiene tres pestañas:

- `Asistente`: permite filtrar productos por categoria, marca y precio.
- `Analisis`: muestra un resumen general de RAM y tarjetas graficas.
- `Recomendador`: muestra las graficas de clustering y sentimiento.

Primero hay que iniciar FastAPI en una terminal:

```powershell
python -m uvicorn api.main:app --reload
```

Despues hay que abrir otra terminal e iniciar Streamlit:

```powershell
python -m streamlit run streamlit_app/streamlit_main.py
```

La aplicacion se abre en `http://localhost:8501`.

Para ejecutar la comprobacion rapida de Streamlit:

```powershell
python check_streamlit.py
```

## Instalacion

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Crear un archivo `.env` en la raiz del proyecto con la conexion local a PostgreSQL:

```text
DATABASE_URL=postgresql://usuario:password@localhost:5432/pccomponentes_ml
```

Para usar AWS RDS, `DATABASE_URL` debe apuntar a la instancia RDS e incluir SSL:

```text
DATABASE_URL=postgresql://usuario:password@host-rds.amazonaws.com:5432/pccomponentes_ml?sslmode=require
```

No subir `.env` a Git. El repositorio mantiene `.env.example` como plantilla.

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
- `fastapi`
- `uvicorn`
- `streamlit`

## Proximos pasos

1. Revisar y documentar ejemplos de uso de la API.
2. Preparar la explicacion academica del flujo PostgreSQL/RDS -> FastAPI -> Streamlit.
3. Preparar la revision final y la presentacion.

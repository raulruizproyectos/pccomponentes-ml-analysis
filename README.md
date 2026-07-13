# PCComponentes ML Analysis

Proyecto académico para extraer, limpiar, guardar y analizar información de memorias RAM y tarjetas gráficas de PcComponentes.

El proyecto incluye scraping, archivos JSON, PostgreSQL en RDS, S3, Lambda, clustering, análisis de sentimiento, FastAPI y una interfaz en Streamlit.

## Integrantes

- Dani
- Raúl
- Andrés

## Guía rápida de evaluación

Esta sección permite comprobar la entrega siguiendo los criterios de `enunciado.md`.

### 1. Preparar el proyecto

Requisitos: Python 3.11 y acceso a una base de datos PostgreSQL con los datos del proyecto.

```powershell
git clone https://github.com/raulruizproyectos/pccomponentes-ml-analysis.git
cd pccomponentes-ml-analysis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `.env` y escribir la conexión recibida por un canal privado:

```text
DATABASE_URL=postgresql://usuario:password@host:5432/pccomponentes_ml?sslmode=require
API_BASE_URL=http://127.0.0.1:8000
```

Las contraseñas y las credenciales de AWS no se guardan en el repositorio.

### 2. Comprobar el código

Esta prueba no modifica datos ni necesita iniciar FastAPI:

```powershell
python check_project.py
```

Comprueba la sintaxis y la integración de Streamlit, el cálculo PCA y la configuración de los disparadores de Lambda.

### 3. Iniciar y comprobar FastAPI

En una terminal:

```powershell
python -m uvicorn api.main:app --reload
```

La documentación interactiva queda disponible en:

```text
http://127.0.0.1:8000/docs
```

En otra terminal:

```powershell
python check_project.py --api
```

Esta orden prueba todos los endpoints principales, incluidos los tres exigidos en el enunciado y el mapa PCA. El producto de ejemplo es `ram_0012`.

### 4. Iniciar Streamlit

Con FastAPI todavía iniciado, abrir otra terminal:

```powershell
python -m streamlit run streamlit_app/streamlit_main.py
```

La aplicación se abre en `http://localhost:8501` y permite comprobar:

- Asistente de preguntas mediante `/ask`.
- Sentimiento, palabras clave, pros y contras mediante `/sentiment`.
- Alternativas del mismo grupo mediante `/similar-products`.
- Mapa interactivo de clústeres mediante PCA.
- Filtros y resúmenes generales del catálogo.

Ejemplo para las tres pestañas:

```text
Producto: Kingston FURY Beast DDR4 3200 MHz 16GB 2x8GB CL16
ID: ram_0012
Pregunta: ¿Cuáles son las quejas más comunes?
```

## Endpoints principales

| Endpoint | Función |
|---|---|
| `GET /health` | Comprueba FastAPI. |
| `GET /db/health` | Comprueba PostgreSQL. |
| `GET /consulta` | Busca y filtra productos. |
| `GET /ask` | Responde preguntas sobre un producto. |
| `GET /sentiment` | Devuelve sentimiento, palabras clave, pros y contras. |
| `GET /similar-products` | Recomienda productos del mismo clúster. |
| `GET /modelos/pca` | Devuelve las coordenadas del mapa PCA. |
| `GET /modelos/clustering` | Resume los grupos de RAM y GPU. |
| `GET /modelos/sentimiento` | Resume el sentimiento de RAM y GPU. |
| `GET /graficas/resumen` | Devuelve indicadores generales. |
| `GET /graficas/precios` | Devuelve datos agregados de precios. |
| `GET /graficas/valoraciones` | Devuelve datos agregados de valoraciones. |

Ejemplos directos:

```text
http://127.0.0.1:8000/sentiment?producto_id=ram_0012
http://127.0.0.1:8000/similar-products?producto_id=ram_0012&limit=5
http://127.0.0.1:8000/ask?producto_id=ram_0012&pregunta=Que%20opinan%20los%20usuarios
http://127.0.0.1:8000/modelos/pca?categoria=memoria_ram
```

## Correspondencia con el enunciado

| Criterio de entrega | Implementación |
|---|---|
| Scraping de productos y reseñas | `scrapers/` y `ejecutar_scraper.py`. |
| Datos brutos y procesados | `data/brutos/` y `data/procesados/`. |
| Limpieza y ETL | `pipeline/` y `aws/lambda_handler.py`. |
| S3, Lambda y PostgreSQL RDS | `aws/`, `database/` y `ejecutar_aws.py`. |
| EDA y preparación de modelos | `notebooks/`. |
| Clustering | K-Means para RAM y GPU, con resultados en PostgreSQL. |
| Análisis de sentimiento | Modelo multilingüe, con resultados en PostgreSQL. |
| API con los tres endpoints pedidos | `api/main.py`. |
| Dashboard y mapa PCA | `streamlit_app/streamlit_main.py`. |
| Despliegue FastAPI en EC2 | Pendiente de completar. |

La preparación inicial del conjunto GPU incluyó una limpieza asistida con IA, autorizada por el profesor. Después se adaptaron y validaron los datos con el código de `pipeline/limpieza_gpu.py`.

## Flujo de datos

```text
PcComponentes
      |
      v
Scraping -> JSON local -> S3 -> Lambda ETL -> PostgreSQL RDS
                                                   |
                                                   v
                                        Modelos y resultados
                                                   |
                                                   v
                                         FastAPI -> Streamlit
```

## AWS

La infraestructura activa utiliza:

- Bucket S3 `pccomponents-bkt` en `eu-north-1`.
- Lambda `pccomponentes-ml-etl` con dos disparadores, uno para RAM y otro para GPU.
- PostgreSQL RDS `database-1`.
- IAM Identity Center para el acceso temporal del equipo.

Comprobaciones locales sin modificar AWS:

```powershell
python ejecutar_aws.py estado
python ejecutar_aws.py etl --categoria todas --dry-run
python check_lambda.py
```

Para comprobar los recursos reales es necesario tener un usuario autorizado en IAM Identity Center:

```powershell
aws sso login --profile nombre-del-perfil
$env:AWS_PROFILE="nombre-del-perfil"
python ejecutar_aws.py verificar-s3
python ejecutar_aws.py verificar-lambda
```

No se deben guardar claves permanentes de AWS en `.env` ni en otros archivos del proyecto.

## Estructura principal

```text
api/             FastAPI y consultas
aws/             S3, Lambda, RDS y orquestación
data/            JSON brutos y procesados
database/        Esquema y consultas PostgreSQL
models/          Modelo guardado
notebooks/       EDA, clustering y sentimiento
pipeline/        Limpieza y carga de datos
scrapers/        Extracción de PcComponentes
streamlit_app/   Interfaz web
check_*.py       Comprobaciones reproducibles
```

## Estado de los datos

### Memorias RAM

- 1646 productos.
- 1574 especificaciones.
- 5876 reseñas con resultado de sentimiento.
- Tres grupos de clustering.

### Tarjetas gráficas

- 500 productos y especificaciones.
- 3564 reseñas con resultado de sentimiento.
- Tres grupos de clustering: alta gama, gama media y ficha incompleta.

## Trabajo pendiente

1. Desplegar FastAPI en EC2 y añadir su URL de evaluación.
2. Restringir el acceso público de RDS después de conectar Lambda y EC2 mediante una red privada.
3. Preparar una demostración final del flujo completo.
4. Configurar y demostrar la ejecución periódica del scraping.

# PCComponentes ML Analysis

Este es un proyecto académico para extraer, limpiar, guardar y analizar datos
de memorias RAM y tarjetas gráficas de PcComponentes.

Incluye scraping, archivos JSON, una base de datos PostgreSQL en RDS, S3,
Lambda, clustering, análisis de sentimiento, una API con FastAPI y una interfaz
hecha con Streamlit.

## Estado de la entrega

El proyecto está terminado y listo para probar. El scraping semanal está
preparado, pero lo dejamos desactivado para evitar consumos automáticos en AWS.
La lista con todas las partes terminadas está en
[`ESTADO_ENTREGA.md`](ESTADO_ENTREGA.md).

## Integrantes

- Dani
- Raúl
- Andrés

## Guía rápida para probar el proyecto

Estos pasos sirven para que el tutor o cualquier miembro del equipo pueda
probar el proyecto.

API desplegada en EC2:

```text
http://13.61.42.45:8000
http://13.61.42.45:8000/docs
```

Estas direcciones son públicas y funcionan desde cualquier IP. Para probarlas
no hace falta entrar en RDS ni tener credenciales de AWS.

### 1. Preparar el proyecto

Se necesita Python 3.11 o una versión superior. Nosotros lo hemos probado con
Python 3.11.

```powershell
git clone https://github.com/raulruizproyectos/pccomponentes-ml-analysis.git
cd pccomponentes-ml-analysis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

El archivo `.env.example` ya utiliza la API pública. Después de copiarlo no
hace falta cambiar esta dirección:

```text
API_BASE_URL=http://13.61.42.45:8000
```

Solo hace falta añadir `DATABASE_URL` si también se quiere iniciar FastAPI en
el ordenador. La conexión real se comparte de forma privada:

```text
DATABASE_URL=postgresql://usuario:password@host:5432/pccomponentes_ml?sslmode=require
API_BASE_URL=http://127.0.0.1:8000
```

Las contraseñas y las credenciales de AWS no se guardan en el repositorio.

### 2. Comprobar el código

Este comando no cambia los datos y tampoco necesita que FastAPI esté iniciado:

```powershell
python check_project.py
```

Comprueba Streamlit, el mapa PCA, Lambda, EC2, el proceso ETL y el scraping
programado.

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

Este comando prueba los endpoints principales, incluidos los tres pedidos en el
enunciado y el mapa PCA. Para la prueba se usa el producto `ram_0012`.

### 4. Iniciar Streamlit

Si se usa FastAPI en local, hay que dejarlo iniciado. Si se usa la API pública,
solo hace falta guardar `API_BASE_URL` en `.env`. Después se ejecuta:

```powershell
python -m streamlit run streamlit_app/streamlit_main.py
```

La aplicación se abre en `http://localhost:8501`. Desde sus tres pestañas se
puede probar:

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
| `GET /modelos/pca` | Devuelve los datos necesarios para dibujar el mapa PCA. |
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

## Dónde está cada parte del proyecto

| Parte pedida | Dónde está |
|---|---|
| Scraping de productos y reseñas | `scrapers/`, `Dockerfile.scraper` y el temporizador de `deploy/`. |
| Datos brutos y procesados | `data/brutos/` y `data/procesados/`. |
| Limpieza y ETL | `pipeline/` y `aws/lambda_handler.py`. |
| S3, Lambda y PostgreSQL RDS | `aws/`, `database/` y `ejecutar_aws.py`. |
| EDA y preparación de modelos | `notebooks/`. |
| Clustering | K-Means para RAM y GPU, con resultados en PostgreSQL. |
| Análisis de sentimiento | Modelo multilingüe, con resultados en PostgreSQL. |
| API con los tres endpoints pedidos | `api/main.py`. |
| Dashboard y mapa PCA | `streamlit_app/streamlit_main.py`. |
| Despliegue FastAPI en EC2 | Instancia pública operativa en `http://13.61.42.45:8000`. |

Para preparar los datos de GPU se hizo una limpieza asistida con IA, autorizada
por el profesor. Después adaptamos y comprobamos los datos con
`pipeline/limpieza_gpu.py`.

## Scraping programado

El proyecto incluye un temporizador que puede hacer cada domingo un scraping
pequeño de una página y cinco productos RAM. Primero sube `listado_ram.json` y
después `detalle_ram.json` a S3. Este segundo archivo activa Lambda una sola vez.

Lo dejamos desactivado para evitar consumos automáticos en la cuenta AWS. El
temporizador de Linux no cuesta dinero, pero cada ejecución utiliza EC2, S3,
Lambda y RDS. Si se quiere usar cada semana, se activa en EC2 con:

```bash
sudo systemctl enable --now pccomponentes-scraper.timer
```

Para probar el flujo una sola vez sin dejarlo programado:

```bash
sudo systemctl start pccomponentes-scraper.service
```

Archivos principales:

- `Dockerfile.scraper`: crea el contenedor con Python 3.11.
- `ejecutar_scraping_programado.py`: ejecuta el scraping y sube los dos JSON.
- `deploy/pccomponentes-scraper.timer`: establece la ejecución semanal.

Para comprobar la configuración sin hacer scraping:

```powershell
python check_scraper.py
```

Para construir el contenedor manualmente:

```powershell
docker build -f Dockerfile.scraper -t pccomponentes-scraper .
```

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

En AWS tenemos estos recursos:

- Bucket S3 `pccomponents-bkt` en `eu-north-1`.
- Lambda `pccomponentes-ml-etl` con dos disparadores, uno para RAM y otro para GPU.
- PostgreSQL RDS `database-1`.
- Lambda conectada a RDS mediante la VPC y un grupo de seguridad propio.
- Endpoint privado de S3 para que Lambda no necesite salida a Internet.
- PostgreSQL cerrado a Internet; solo acceden Lambda, EC2 y las IP autorizadas del equipo.
- IAM Identity Center para el acceso temporal del equipo.

Estos comandos comprueban la configuración sin cambiar nada en AWS:

```powershell
python ejecutar_aws.py estado
python ejecutar_aws.py etl --categoria todas --dry-run
python check_lambda.py
```

Para comprobar los recursos reales hace falta un usuario autorizado en IAM
Identity Center:

```powershell
aws sso login --profile nombre-del-perfil
$env:AWS_PROFILE="nombre-del-perfil"
python ejecutar_aws.py verificar-s3
python ejecutar_aws.py verificar-lambda
```

Si hay que volver a preparar la red privada de Lambda, se usa:

```powershell
python ejecutar_aws.py asegurar-red-lambda
```

No guardamos credenciales permanentes de AWS en `.env` ni en ningún archivo
del proyecto.

Para probar el flujo completo usamos estos dos archivos de S3:

```text
brutos/ram/detalle_ram.json
brutos/tarjetas_graficas/tarjetas_graficas.json
```

Lambda limpió los datos y actualizó en RDS 1646 productos RAM y 500 tarjetas
gráficas sin duplicar los registros que ya existían.

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
check_*.py       Pruebas sencillas del proyecto
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

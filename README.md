# PCComponentes ML Analysis

Proyecto para recoger y analizar datos de componentes de PCComponentes.

En este proyecto trabajamos con memorias RAM y tarjetas gráficas. Recogemos los datos, los limpiamos, los guardamos en PostgreSQL y después los utilizamos para hacer análisis y modelos de Machine Learning.

## Integrantes

- Dani
- Raúl
- Andrés

## Proceso del proyecto

Los pasos que seguimos son:

1. Extraer los datos de PCComponentes.
2. Guardar los datos brutos en archivos JSON.
3. Limpiar los datos.
4. Guardar los datos limpios en PostgreSQL.
5. Analizar los datos con notebooks.
6. Preparar los datos para los modelos.
7. Entrenar y guardar los modelos.

## Estado actual

En la parte de memorias RAM ya hemos realizado:

- La extracción de productos, características y reseñas.
- La limpieza de los datos.
- La corrección de textos y capacidades incorrectas.
- La creación de las tablas de PostgreSQL.
- La carga de los datos limpios en PostgreSQL.
- El análisis de los datos brutos.
- El análisis de los datos limpios mediante consultas a PostgreSQL.
- Un modelo de clustering para agrupar productos RAM.
- Un análisis básico del texto de las reseñas de RAM.

Actualmente tenemos:

- 1646 productos.
- 1574 registros de características.
- 1574 distribuciones de valoraciones.
- 5876 reseñas.

El modelo de clustering separa las memorias RAM en tres grupos:

- RAM básica.
- DDR5 estándar.
- DDR5 de alta capacidad.

## Estructura principal

```text
pccomponentes-ml-analysis/
├── data/
│   ├── brutos/
│   └── procesados/
├── database/
│   ├── conexion.py
│   ├── esquema.sql
│   ├── inserciones.py
│   └── inserciones_ram.py
├── docs/
├── models/
│   └── modelo_clustering_ram.joblib
├── notebooks/
│   ├── 01_eda_ram.ipynb
│   ├── 02_eda_tarjetas_graficas.ipynb
│   ├── 03_conexion_postgresql.ipynb
│   ├── 04_eda_ram_datos_limpios.ipynb
│   ├── 05_preparacion_modelo_ram.ipynb
│   └── 06_nlp_resenas_ram.ipynb
├── pipeline/
│   ├── carga_ram_postgresql.py
│   ├── etl_processor.py
│   └── limpieza_ram.py
├── scrapers/
├── ejecutar_scraper.py
├── requirements.txt
└── README.md
```

## Notebooks

### 01_eda_ram.ipynb

Análisis inicial de los datos brutos de memorias RAM.

### 02_eda_tarjetas_graficas.ipynb

Notebook para analizar los datos de tarjetas gráficas.

### 03_conexion_postgresql.ipynb

Pruebas de conexión con PostgreSQL.

### 04_eda_ram_datos_limpios.ipynb

Análisis de los datos limpios de RAM. Los datos se obtienen haciendo consultas a PostgreSQL.

### 05_preparacion_modelo_ram.ipynb

Preparación de los datos y creación del modelo de clustering de RAM.

### 06_nlp_resenas_ram.ipynb

Análisis de las reseñas de RAM. Se revisan las palabras más frecuentes, los pros, los contras y la distribución de las valoraciones.

## Instalación

Para instalar las librerías necesarias:

```powershell
pip install -r requirements.txt
```

También es necesario tener PostgreSQL instalado y crear la base de datos del proyecto.

## Limpieza de los datos RAM

Para volver a generar los archivos limpios:

```powershell
python -B pipeline/limpieza_ram.py
```

Los archivos se guardan en:

```text
data/procesados/ram/
```

## Base de datos

El esquema de PostgreSQL está en:

```text
database/esquema.sql
```

La carga de los datos de RAM se realiza desde:

```text
pipeline/carga_ram_postgresql.py
```

Las tablas utilizadas son:

- `productos`
- `especificaciones_ram`
- `distribucion_valoraciones`
- `resenas`
- `especificaciones_gpu`

## Modelo de clustering

El modelo agrupa las memorias RAM utilizando estas características:

- Precio.
- Capacidad.
- Frecuencia.
- Latencia.
- Tipo de memoria.

El modelo creado se guarda en:

```text
models/modelo_clustering_ram.joblib
```

## Próximos pasos

- Continuar con los datos de tarjetas gráficas.
- Repetir el análisis de reseñas con los datos de GPU.
- Crear la API con FastAPI.
- Preparar la aplicación con Streamlit.
- Conectar el proyecto con los servicios de AWS.

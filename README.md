# pccomponentes-ml-analysis

Proyecto para recoger y analizar datos de productos de PcComponentes.

De momento estamos trabajando con dos tipos de productos:

- Tarjetas graficas.
- Memorias RAM.

La idea es guardar los productos, sus especificaciones, valoraciones y resenas en PostgreSQL. Mas adelante usaremos estos datos para hacer analisis y modelos de Machine Learning.

## Integrantes

- Dani
- Raul
- Andres

## Estado actual

Ya tenemos preparada una base de datos local llamada `pccomponentes_ml`.

Las tablas actuales son:

- `productos`: datos comunes de todos los productos.
- `especificaciones_gpu`: datos tecnicos de tarjetas graficas.
- `especificaciones_ram`: datos tecnicos de memorias RAM.
- `distribucion_valoraciones`: cantidad de valoraciones de 1 a 5 estrellas.
- `resenas`: opiniones de los usuarios.

La tabla `productos` tiene una columna llamada `categoria` para distinguir:

- `tarjeta_grafica`
- `memoria_ram`

Tambien se han probado las funciones de insercion y consulta con dos tarjetas graficas y una memoria RAM.

## Estructura principal

```text
pccomponentes-ml-analysis/
|-- README.md
|-- requirements.txt
|-- configuracion.local
|-- ejecutar_scraper.py
|-- database/
|   |-- esquema.sql
|   |-- conexion.py
|   |-- consultas.py
|   `-- inserciones.py
|-- config/
|   `-- settings.py
|-- scrapers/
|   |-- listado.py
|   |-- detalle.py
|   `-- utilidades.py
|-- pipeline/
|   `-- etl_processor.py
|-- notebooks/
|   |-- 01_eda_ram.ipynb
|   |-- 02_eda_tarjetas_graficas.ipynb
|   |-- 03_conexion_postgresql.ipynb
|   `-- 04_validacion_database.ipynb
|-- docs/
|   |-- fuentes_tarjetas_graficas.md
|   `-- fuentes_memorias_ram.md
`-- comun/
    |-- datos/
    `-- codigo/
```

## Archivos de base de datos

`database/esquema.sql`

Contiene el SQL necesario para crear las tablas desde cero.

`database/conexion.py`

Contiene la funcion para conectar Python con PostgreSQL.

`database/inserciones.py`

Contiene funciones para insertar:

- Productos.
- Especificaciones GPU.
- Especificaciones RAM.
- Distribuciones de valoraciones.
- Resenas.

`database/consultas.py`

Contiene funciones para consultar productos, especificaciones, resumenes y resenas.

## Documentacion de productos

En la carpeta `docs/` guardamos los datos recogidos manualmente desde PcComponentes.

Solo usamos datos que aparecen en PcComponentes. Si un dato no aparece, se escribe `NULL`. Cuando se prepara ese dato en Python se utiliza `None`.

## Instalacion

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Despues hay que crear la base de datos `pccomponentes_ml` en PostgreSQL y ejecutar:

```text
database/esquema.sql
```

Los datos de conexion se guardan de forma local y no se deben subir a GitHub.

## Uso de los notebooks

Los notebooks se utilizan solo para hacer pruebas y revisar resultados.

El codigo principal debe quedar en:

- `database/`
- `scrapers/`
- `pipeline/`

## Siguiente paso

El siguiente paso es empezar el scraper de memorias RAM con una sola URL, guardar el HTML y comprobar la extraccion antes de hacer pruebas con mas productos.

# API principal del proyecto.
from decimal import Decimal

from fastapi import FastAPI

from config.settings import DATABASE_URL
from database.conexion import conectar_postgresql

app = FastAPI(title="PCComponentes ML API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db/health")
def db_health():
    conn = conectar_postgresql(DATABASE_URL)
    conn.close()

    return {"database": "ok"}


# Consulta productos desde PostgreSQL y los devuelve como JSON.
@app.get("/consulta")
def consulta_productos(
    categoria: str | None = None,
    marca: str | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    orden: str = "precio",
    limit: int = 10,
):
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    if limit > 50:
        limit = 50

    if limit < 1:
        limit = 1

    columnas_orden = {
        "precio": "precio ASC",
        "valoracion": "valoracion_media DESC",
        "opiniones": "total_opiniones DESC",
    }

    orden_sql = columnas_orden.get(orden, "precio ASC")

    condiciones = []
    parametros = []

    if categoria:
        condiciones.append("categoria = %s")
        parametros.append(categoria)

    if marca:
        condiciones.append("marca = %s")
        parametros.append(marca)

    if precio_min:
        condiciones.append("precio >= %s")
        parametros.append(precio_min)

    if precio_max:
        condiciones.append("precio <= %s")
        parametros.append(precio_max)

    where_sql = ""

    if condiciones:
        where_sql = "WHERE " + " AND ".join(condiciones)

    parametros.append(limit)

    cursor.execute(f"""
        SELECT producto_id, nombre, marca, categoria, precio, valoracion_media, total_opiniones
        FROM productos
        {where_sql}
        ORDER BY {orden_sql}
        LIMIT %s;
    """, parametros)

    productos = cursor.fetchall()
    conn.close()

    resultado = []

    for producto in productos:
        resultado.append({
            "producto_id": producto[0],
            "nombre": producto[1],
            "marca": producto[2],
            "categoria": producto[3],
            "precio": float(producto[4]) if isinstance(producto[4], Decimal) else producto[4],
            "valoracion_media": float(producto[5]) if isinstance(producto[5], Decimal) else producto[5],
            "total_opiniones": producto[6],
        })

    return resultado


# Resume cuantos resultados hay guardados de clustering y sentimiento.
@app.get("/modelos")
def resumen_modelos():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM resultados_clustering_ram;")
    clustering_ram = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resultados_clustering_gpu;")
    clustering_gpu = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resultados_sentimiento;")
    sentimiento_ram = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM resultados_sentimiento_gpu;")
    sentimiento_gpu = cursor.fetchone()[0]

    conn.close()

    return {
        "clustering_ram": clustering_ram,
        "clustering_gpu": clustering_gpu,
        "sentimiento_ram": sentimiento_ram,
        "sentimiento_gpu": sentimiento_gpu,
    }


# Resume los grupos creados por el modelo de clustering.
@app.get("/modelos/clustering")
def resumen_clustering():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre_grupo, COUNT(*)
        FROM resultados_clustering_ram
        GROUP BY nombre_grupo
        ORDER BY nombre_grupo;
    """)

    grupos_ram = cursor.fetchall()

    cursor.execute("""
        SELECT nombre_grupo, COUNT(*)
        FROM resultados_clustering_gpu
        GROUP BY nombre_grupo
        ORDER BY nombre_grupo;
    """)

    grupos_gpu = cursor.fetchall()
    conn.close()

    return {
        "ram": [
            {"nombre_grupo": grupo[0], "total": grupo[1]}
            for grupo in grupos_ram
        ],
        "gpu": [
            {"nombre_grupo": grupo[0], "total": grupo[1]}
            for grupo in grupos_gpu
        ],
    }


# Resume los resultados del modelo de sentimiento.
@app.get("/modelos/sentimiento")
def resumen_sentimiento():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sentimiento, COUNT(*)
        FROM resultados_sentimiento
        GROUP BY sentimiento
        ORDER BY sentimiento;
    """)

    sentimiento_ram = cursor.fetchall()

    cursor.execute("""
        SELECT sentimiento, COUNT(*)
        FROM resultados_sentimiento_gpu
        GROUP BY sentimiento
        ORDER BY sentimiento;
    """)

    sentimiento_gpu = cursor.fetchall()
    conn.close()

    return {
        "ram": [
            {"sentimiento": fila[0], "total": fila[1]}
            for fila in sentimiento_ram
        ],
        "gpu": [
            {"sentimiento": fila[0], "total": fila[1]}
            for fila in sentimiento_gpu
        ],
    }


# Devuelve datos agregados para construir graficas generales.
@app.get("/graficas/resumen")
def resumen_graficas():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            categoria,
            COUNT(*),
            AVG(precio),
            AVG(valoracion_media),
            SUM(total_opiniones)
        FROM productos
        GROUP BY categoria
        ORDER BY categoria;
    """)

    filas = cursor.fetchall()
    conn.close()

    resultado = []

    for fila in filas:
        resultado.append({
            "categoria": fila[0],
            "total_productos": fila[1],
            "precio_medio": float(fila[2]) if isinstance(fila[2], Decimal) else fila[2],
            "valoracion_media": float(fila[3]) if isinstance(fila[3], Decimal) else fila[3],
            "total_opiniones": fila[4],
        })

    return resultado


# Agrupa productos por rangos de precio para graficas.
@app.get("/graficas/precios")
def graficas_precios():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            categoria,
            CASE
                WHEN precio < 100 THEN '0-100'
                WHEN precio < 500 THEN '100-500'
                WHEN precio < 1000 THEN '500-1000'
                ELSE '1000+'
            END AS rango,
            COUNT(*)
        FROM productos
        GROUP BY categoria, rango
        ORDER BY categoria, rango;
    """)

    filas = cursor.fetchall()
    conn.close()

    resultado = {
        "memoria_ram": [],
        "tarjeta_grafica": [],
    }

    for fila in filas:
        resultado[fila[0]].append({
            "rango": fila[1],
            "total": fila[2],
        })

    return resultado


# Agrupa productos por rangos de valoracion media para graficas.
@app.get("/graficas/valoraciones")
def graficas_valoraciones():
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            categoria,
            CASE
                WHEN valoracion_media IS NULL THEN 'sin_valoracion'
                WHEN valoracion_media < 2 THEN '0-2'
                WHEN valoracion_media < 3 THEN '2-3'
                WHEN valoracion_media < 4 THEN '3-4'
                ELSE '4-5'
            END AS rango,
            COUNT(*)
        FROM productos
        GROUP BY categoria, rango
        ORDER BY categoria, rango;
    """)

    filas = cursor.fetchall()
    conn.close()

    resultado = {
        "memoria_ram": [],
        "tarjeta_grafica": [],
    }

    for fila in filas:
        resultado[fila[0]].append({
            "rango": fila[1],
            "total": fila[2],
        })

    return resultado

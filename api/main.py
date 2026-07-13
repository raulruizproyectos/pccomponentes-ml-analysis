# API principal del proyecto.
from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal

import pandas as pd
from fastapi import FastAPI, HTTPException
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from config.settings import DATABASE_URL
from database.conexion import conectar_postgresql

app = FastAPI(title="PCComponentes ML API")

PALABRAS_COMUNES = {
    "aunque",
    "como",
    "cuando",
    "desde",
    "esta",
    "este",
    "estos",
    "estas",
    "hacer",
    "nada",
    "para",
    "pero",
    "porque",
    "producto",
    "sobre",
    "tambien",
    "también",
    "tiene",
    "todo",
}


def extraer_palabras_clave(textos, limite=10):
    palabras = []

    for texto in textos:
        palabras.extend(re.findall(r"[a-záéíóúüñ]{4,}", texto.lower()))

    conteo = Counter(
        palabra
        for palabra in palabras
        if palabra not in PALABRAS_COMUNES
    )

    return [
        {"palabra": palabra, "total": total}
        for palabra, total in conteo.most_common(limite)
    ]


def calcular_coordenadas_pca(datos, columnas_numericas, columnas_categoricas):
    matriz_numerica = datos[columnas_numericas].copy()

    for columna in columnas_numericas:
        matriz_numerica[columna] = pd.to_numeric(
            matriz_numerica[columna],
            errors="coerce",
        )
        matriz_numerica[columna] = (
            matriz_numerica[columna]
            .fillna(matriz_numerica[columna].median())
            .fillna(0)
        )

    matriz_categorica = pd.get_dummies(
        datos[columnas_categoricas].fillna("Sin identificar"),
        dtype=int,
    )
    matriz = pd.concat([matriz_numerica, matriz_categorica], axis=1)
    matriz_escalada = StandardScaler().fit_transform(matriz)
    coordenadas = PCA(n_components=2).fit_transform(matriz_escalada)

    resultado = datos.copy()
    resultado["pca_1"] = coordenadas[:, 0]
    resultado["pca_2"] = coordenadas[:, 1]
    return resultado


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
    texto: str | None = None,
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

    if texto and texto.strip():
        condiciones.append("nombre ILIKE %s")
        parametros.append(f"%{texto.strip()}%")

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


# Devuelve el sentimiento y los comentarios principales de un producto.
@app.get("/sentiment")
def sentimiento_producto(producto_id: str):
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, categoria
        FROM productos
        WHERE producto_id = %s;
    """, (producto_id,))

    producto = cursor.fetchone()

    if not producto:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    tablas = {
        "memoria_ram": ("resenas", "resultados_sentimiento"),
        "tarjeta_grafica": ("resenas_gpu", "resultados_sentimiento_gpu"),
    }

    tabla_resenas, tabla_sentimiento = tablas[producto[1]]

    cursor.execute(f"""
        SELECT r.texto_resena, r.pros, r.contras, s.sentimiento
        FROM {tabla_resenas} r
        JOIN {tabla_sentimiento} s
            ON r.resena_id = s.resena_id
        WHERE r.producto_id = %s;
    """, (producto_id,))

    filas = cursor.fetchall()
    conn.close()

    total_resenas = len(filas)
    conteos = Counter(fila[3] for fila in filas)

    sentimientos = []

    for nombre in ("negativo", "neutral", "positivo"):
        total = conteos.get(nombre, 0)
        porcentaje = round(total * 100 / total_resenas, 2) if total_resenas else 0
        sentimientos.append({
            "sentimiento": nombre,
            "total": total,
            "porcentaje": porcentaje,
        })

    textos = [
        " ".join(valor for valor in fila[:3] if valor)
        for fila in filas
    ]

    pros = list(dict.fromkeys(
        fila[1].strip()
        for fila in filas
        if fila[1] and fila[1].strip()
    ))[:5]

    contras = list(dict.fromkeys(
        fila[2].strip()
        for fila in filas
        if fila[2] and fila[2].strip()
    ))[:5]

    return {
        "producto_id": producto_id,
        "nombre": producto[0],
        "categoria": producto[1],
        "total_resenas": total_resenas,
        "sentimientos": sentimientos,
        "palabras_clave": extraer_palabras_clave(textos),
        "pros": pros,
        "contras": contras,
    }


# Recomienda otros productos que pertenecen al mismo grupo.
@app.get("/similar-products")
def productos_similares(producto_id: str, limit: int = 5):
    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nombre, categoria
        FROM productos
        WHERE producto_id = %s;
    """, (producto_id,))

    producto = cursor.fetchone()

    if not producto:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    tablas = {
        "memoria_ram": (
            "resultados_clustering_ram",
            "resenas",
            "resultados_sentimiento",
        ),
        "tarjeta_grafica": (
            "resultados_clustering_gpu",
            "resenas_gpu",
            "resultados_sentimiento_gpu",
        ),
    }

    tabla_clustering, tabla_resenas, tabla_sentimiento = tablas[producto[1]]

    cursor.execute(f"""
        SELECT grupo, nombre_grupo
        FROM {tabla_clustering}
        WHERE producto_id = %s;
    """, (producto_id,))

    grupo = cursor.fetchone()

    if not grupo:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto sin resultado de clustering")

    limit = max(1, min(limit, 20))

    cursor.execute(f"""
        SELECT
            p.producto_id,
            p.nombre,
            p.marca,
            p.precio,
            p.valoracion_media,
            p.total_opiniones,
            COALESCE(sentimiento.porcentaje_positivo, 0)
        FROM productos p
        JOIN {tabla_clustering} clustering
            ON p.producto_id = clustering.producto_id
        LEFT JOIN (
            SELECT
                r.producto_id,
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE s.sentimiento = 'positivo')
                    / NULLIF(COUNT(*), 0),
                    2
                ) AS porcentaje_positivo
            FROM {tabla_resenas} r
            JOIN {tabla_sentimiento} s
                ON r.resena_id = s.resena_id
            GROUP BY r.producto_id
        ) sentimiento
            ON p.producto_id = sentimiento.producto_id
        WHERE clustering.grupo = %s
            AND p.producto_id <> %s
        ORDER BY
            sentimiento.porcentaje_positivo DESC NULLS LAST,
            p.valoracion_media DESC NULLS LAST,
            p.total_opiniones DESC
        LIMIT %s;
    """, (grupo[0], producto_id, limit))

    filas = cursor.fetchall()
    conn.close()

    similares = []

    for fila in filas:
        similares.append({
            "producto_id": fila[0],
            "nombre": fila[1],
            "marca": fila[2],
            "precio": float(fila[3]) if isinstance(fila[3], Decimal) else fila[3],
            "valoracion_media": float(fila[4]) if isinstance(fila[4], Decimal) else fila[4],
            "total_opiniones": fila[5],
            "porcentaje_positivo": float(fila[6]),
        })

    return {
        "producto_origen": {
            "producto_id": producto_id,
            "nombre": producto[0],
            "categoria": producto[1],
            "grupo": grupo[0],
            "nombre_grupo": grupo[1],
        },
        "similares": similares,
    }


# Responde preguntas sencillas usando sentimiento y clustering.
@app.get("/ask")
def preguntar_producto(producto_id: str, pregunta: str):
    pregunta = pregunta.strip()

    if len(pregunta) < 3:
        raise HTTPException(status_code=400, detail="La pregunta es demasiado corta")

    if len(pregunta) > 300:
        raise HTTPException(status_code=400, detail="La pregunta es demasiado larga")

    texto = pregunta.lower()

    if any(palabra in texto for palabra in (
        "similar",
        "alternativa",
        "recomienda",
        "parecido",
    )):
        resultado = productos_similares(producto_id, limit=5)
        nombres = [producto["nombre"] for producto in resultado["similares"]]

        return {
            "producto_id": producto_id,
            "pregunta": pregunta,
            "tipo_respuesta": "recomendacion",
            "respuesta": "Alternativas del mismo grupo: " + "; ".join(nombres),
            "datos": resultado["similares"],
        }

    resultado = sentimiento_producto(producto_id)
    porcentajes = {
        fila["sentimiento"]: fila["porcentaje"]
        for fila in resultado["sentimientos"]
    }

    if any(palabra in texto for palabra in (
        "queja",
        "problema",
        "contra",
        "malo",
        "negativ",
    )):
        contras = resultado["contras"][:3]
        detalle = "; ".join(contras) if contras else "No hay contras escritos."

        return {
            "producto_id": producto_id,
            "pregunta": pregunta,
            "tipo_respuesta": "quejas",
            "respuesta": (
                f"El {porcentajes['negativo']}% de las reseñas analizadas "
                f"son negativas. Quejas encontradas: {detalle}"
            ),
            "datos": {
                "porcentaje_negativo": porcentajes["negativo"],
                "contras": contras,
            },
        }

    if any(palabra in texto for palabra in (
        "ventaja",
        "bueno",
        "buena",
        "positivo",
        "positiva",
        "pros",
    )):
        pros = resultado["pros"][:3]
        detalle = "; ".join(pros) if pros else "No hay ventajas escritas."

        return {
            "producto_id": producto_id,
            "pregunta": pregunta,
            "tipo_respuesta": "ventajas",
            "respuesta": (
                f"El {porcentajes['positivo']}% de las reseñas analizadas "
                f"son positivas. Ventajas encontradas: {detalle}"
            ),
            "datos": {
                "porcentaje_positivo": porcentajes["positivo"],
                "pros": pros,
            },
        }

    palabras = ", ".join(
        fila["palabra"]
        for fila in resultado["palabras_clave"][:5]
    )

    return {
        "producto_id": producto_id,
        "pregunta": pregunta,
        "tipo_respuesta": "resumen",
        "respuesta": (
            f"Se analizaron {resultado['total_resenas']} reseñas: "
            f"{porcentajes['positivo']}% positivas, "
            f"{porcentajes['neutral']}% neutrales y "
            f"{porcentajes['negativo']}% negativas. "
            f"Palabras frecuentes: {palabras}."
        ),
        "datos": resultado,
    }


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


# Reduce las caracteristicas de cada producto a dos coordenadas para el mapa.
@app.get("/modelos/pca")
def mapa_pca(categoria: str = "memoria_ram"):
    if categoria not in ("memoria_ram", "tarjeta_grafica"):
        raise HTTPException(status_code=400, detail="Categoria no valida")

    conn = conectar_postgresql(DATABASE_URL)
    cursor = conn.cursor()

    if categoria == "memoria_ram":
        cursor.execute("""
            SELECT
                p.producto_id,
                p.nombre,
                p.precio,
                e.capacidad_gb,
                e.frecuencia_mhz,
                e.latencia_cl,
                e.tipo_memoria,
                c.grupo,
                c.nombre_grupo
            FROM productos p
            JOIN especificaciones_ram e ON p.producto_id = e.producto_id
            JOIN resultados_clustering_ram c ON p.producto_id = c.producto_id;
        """)
        columnas = [
            "producto_id",
            "nombre",
            "precio",
            "capacidad_gb",
            "frecuencia_mhz",
            "latencia_cl",
            "tipo_memoria",
            "grupo",
            "nombre_grupo",
        ]
        columnas_numericas = [
            "precio",
            "capacidad_gb",
            "frecuencia_mhz",
            "latencia_cl",
        ]
    else:
        cursor.execute("""
            SELECT
                p.producto_id,
                p.nombre,
                p.precio,
                p.valoracion_media,
                p.total_opiniones,
                p.porcentaje_recomendacion,
                e.memoria_vram,
                e.tipo_memoria,
                e.bus_memoria,
                c.grupo,
                c.nombre_grupo
            FROM productos p
            JOIN especificaciones_gpu e ON p.producto_id = e.producto_id
            JOIN resultados_clustering_gpu c ON p.producto_id = c.producto_id;
        """)
        columnas = [
            "producto_id",
            "nombre",
            "precio",
            "valoracion_media",
            "total_opiniones",
            "porcentaje_recomendacion",
            "memoria_vram",
            "tipo_memoria",
            "bus_memoria",
            "grupo",
            "nombre_grupo",
        ]
        columnas_numericas = [
            "precio",
            "valoracion_media",
            "total_opiniones",
            "porcentaje_recomendacion",
            "memoria_vram_gb",
            "bus_memoria_bits",
        ]

    filas = cursor.fetchall()
    conn.close()

    if len(filas) < 2:
        raise HTTPException(status_code=404, detail="No hay datos suficientes para PCA")

    datos = pd.DataFrame(filas, columns=columnas)

    if categoria == "tarjeta_grafica":
        datos["memoria_vram_gb"] = pd.to_numeric(
            datos["memoria_vram"].astype("string").str.extract(r"(\d+)")[0],
            errors="coerce",
        )
        datos["bus_memoria_bits"] = pd.to_numeric(
            datos["bus_memoria"].astype("string").str.extract(r"(\d+)")[0],
            errors="coerce",
        )

    datos = calcular_coordenadas_pca(
        datos,
        columnas_numericas,
        ["tipo_memoria"],
    )

    productos = []

    for _, producto in datos.iterrows():
        productos.append({
            "producto_id": producto["producto_id"],
            "nombre": producto["nombre"],
            "precio": float(producto["precio"]),
            "grupo": int(producto["grupo"]),
            "nombre_grupo": producto["nombre_grupo"],
            "pca_1": round(float(producto["pca_1"]), 4),
            "pca_2": round(float(producto["pca_2"]), 4),
        })

    return {
        "categoria": categoria,
        "total_productos": len(productos),
        "productos": productos,
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

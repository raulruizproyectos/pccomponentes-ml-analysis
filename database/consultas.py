# Este módulo contiene funciones para realizar consultas a la base de datos PostgreSQL.

def obtener_productos(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT producto_id, categoria, modelo, precio
        FROM productos
        ORDER BY producto_id;
    """)

    productos = cursor.fetchall()

    return productos

# Función para obtener las reseñas de un producto específico

def obtener_resenas_por_producto(conn, producto_id):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.modelo,
            r.usuario,
            r.valoracion,
            r.texto_resena,
            r.pros,
            r.contras
        FROM productos p
        JOIN resenas r
            ON p.producto_id = r.producto_id
        WHERE p.producto_id = %s;
    """, (producto_id,))

    resenas = cursor.fetchall()

    return resenas

# Función para obtener los productos junto con sus especificaciones técnicas de las GPU (si las tienen)

def obtener_productos_con_especificaciones_gpu(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.producto_id,
            p.modelo,
            p.precio,
            e.gpu,
            e.memoria_vram,
            e.tipo_memoria,
            e.bus_memoria
        FROM productos p
        JOIN especificaciones_gpu e
            ON p.producto_id = e.producto_id
        ORDER BY p.producto_id;
    """)

    productos = cursor.fetchall()

    return productos

# Función para obtener los productos junto con sus especificaciones técnicas de las RAM (si las tienen)

def obtener_productos_con_especificaciones_ram(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.producto_id,
            p.modelo,
            p.precio,
            e.memoria_interna,
            e.diseno_memoria,
            e.tipo_memoria,
            e.velocidad_frecuencia,
            e.voltaje,
            e.compatibilidad
        FROM productos p
        JOIN especificaciones_ram e
            ON p.producto_id = e.producto_id
        ORDER BY p.producto_id;
    """)

    productos_ram = cursor.fetchall()

    return productos_ram


# Función para obtener la distribución de valoraciones (número de reseñas por cada cantidad de estrellas) para cada producto

def obtener_distribucion_valoraciones(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            producto_id,
            estrellas_5,
            estrellas_4,
            estrellas_3,
            estrellas_2,
            estrellas_1
        FROM distribucion_valoraciones
        ORDER BY producto_id;
    """)

    distribuciones = cursor.fetchall()

    return distribuciones

# Función para obtener un resumen de los productos con sus especificaciones técnicas de GPU y la distribución de valoraciones

def obtener_resumen_productos_gpu(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.producto_id,
            p.modelo,
            p.marca,
            p.precio,
            p.valoracion_media,
            p.numero_total_opiniones,
            p.porcentaje_recomendacion,
            e.gpu,
            e.memoria_vram,
            e.tipo_memoria,
            e.bus_memoria,
            d.estrellas_5,
            d.estrellas_4,
            d.estrellas_3,
            d.estrellas_2,
            d.estrellas_1
        FROM productos p
        JOIN especificaciones_gpu e
            ON p.producto_id = e.producto_id
        JOIN distribucion_valoraciones d
            ON p.producto_id = d.producto_id
        ORDER BY p.producto_id;
    """)

    resumen_productos_gpu = cursor.fetchall()

    return resumen_productos_gpu


# Función para obtener un resumen de los productos RAM con sus especificaciones y distribución de valoraciones

def obtener_resumen_productos_ram(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.producto_id,
            p.modelo,
            p.marca,
            p.precio,
            p.valoracion_media,
            p.numero_total_opiniones,
            p.porcentaje_recomendacion,
            e.memoria_interna,
            e.diseno_memoria,
            e.tipo_memoria,
            e.velocidad_frecuencia,
            e.voltaje,
            e.compatibilidad,
            d.estrellas_5,
            d.estrellas_4,
            d.estrellas_3,
            d.estrellas_2,
            d.estrellas_1
        FROM productos p
        JOIN especificaciones_ram e
            ON p.producto_id = e.producto_id
        JOIN distribucion_valoraciones d
            ON p.producto_id = d.producto_id
        ORDER BY p.producto_id;
    """)

    resumen_productos_ram = cursor.fetchall()

    return resumen_productos_ram


# Función para obtener las reseñas junto con los datos del producto al que pertenecen

def obtener_resenas_con_producto(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.resena_id,
            p.producto_id,
            p.modelo,
            p.marca,
            p.categoria,
            r.usuario,
            r.valoracion,
            r.texto_resena,
            r.pros,
            r.contras
        FROM resenas r
        JOIN productos p
            ON r.producto_id = p.producto_id
        ORDER BY r.resena_id;
    """)

    resenas = cursor.fetchall()

    return resenas

# Función para obtener las reseñas de una categoría específica junto con los datos del producto al que pertenecen

def obtener_resenas_por_categoria(conn, categoria):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.resena_id,
            p.producto_id,
            p.modelo,
            p.categoria,
            r.usuario,
            r.valoracion,
            r.texto_resena,
            r.pros,
            r.contras
        FROM resenas r
        JOIN productos p
            ON r.producto_id = p.producto_id
        WHERE p.categoria = %s
        ORDER BY r.resena_id;
    """, (categoria,))

    resenas = cursor.fetchall()

    return resenas
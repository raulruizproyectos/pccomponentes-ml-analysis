# Este módulo contiene funciones para insertar datos en la base de datos PostgreSQL.

def insertar_resenas(conn, data_resenas):
    cursor = conn.cursor()

    cursor.executemany(
        query="""
            INSERT INTO resenas (
                producto_id,
                usuario,
                valoracion,
                opinion_verificada,
                opinion_destacada,
                fecha_resena_texto,
                variante_modelo,
                color,
                texto_resena,
                pros,
                contras,
                likes,
                numero_respuestas,
                tiene_imagen
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        params_seq=data_resenas
    )

    conn.commit()


def insertar_productos(conn, data_productos):
    cursor = conn.cursor()

    cursor.executemany(
        query="""
            INSERT INTO productos (
                url,
                modelo,
                marca,
                precio,
                valoracion_media,
                numero_total_opiniones,
                porcentaje_recomendacion,
                numero_recomendaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        params_seq=data_productos
    )

    conn.commit()


def insertar_especificaciones(conn, data_especificaciones):
    cursor = conn.cursor()

    cursor.executemany(
        query="""
            INSERT INTO especificaciones_producto (
                producto_id,
                gpu,
                memoria_vram,
                tipo_memoria,
                bus_memoria,
                ancho_banda_memoria,
                velocidad_memoria,
                reloj_base,
                reloj_boost,
                salidas_video,
                resolucion_maxima
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        params_seq=data_especificaciones
    )

    conn.commit()


def insertar_distribucion_valoraciones(conn, data_distribucion):
    cursor = conn.cursor()

    cursor.executemany(
        query="""
            INSERT INTO distribucion_valoraciones (
                producto_id,
                estrellas_5,
                estrellas_4,
                estrellas_3,
                estrellas_2,
                estrellas_1
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        """,
        params_seq=data_distribucion
    )

    conn.commit()
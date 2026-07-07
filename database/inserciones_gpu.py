# Inserciones de datos limpios de GPU en PostgreSQL.


def insertar_productos_gpu(conn, data_productos):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO productos (
                producto_id,
                nombre,
                url,
                sku,
                marca,
                categoria,
                precio,
                moneda,
                valoracion_media,
                total_opiniones,
                total_resenas_con_texto,
                porcentaje_recomendacion,
                numero_recomendaciones,
                pagina_origen,
                posicion_listado,
                presente_en_detalle,
                fuente
            )
            VALUES (
                %(producto_id)s,
                %(nombre)s,
                %(url)s,
                %(sku)s,
                %(marca)s,
                %(categoria)s,
                %(precio)s,
                %(moneda)s,
                %(valoracion_media)s,
                %(total_opiniones)s,
                %(total_resenas_con_texto)s,
                %(porcentaje_recomendacion)s,
                %(numero_recomendaciones)s,
                %(pagina_origen)s,
                %(posicion_listado)s,
                %(presente_en_detalle)s,
                %(fuente)s
            );
            """,
            data_productos,
        )


def insertar_especificaciones_gpu(conn, data_especificaciones):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO especificaciones_gpu (
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
            VALUES (
                %(producto_id)s,
                %(gpu)s,
                %(memoria_vram)s,
                %(tipo_memoria)s,
                %(bus_memoria)s,
                %(ancho_banda_memoria)s,
                %(velocidad_memoria)s,
                %(reloj_base)s,
                %(reloj_boost)s,
                %(salidas_video)s,
                %(resolucion_maxima)s
            );
            """,
            data_especificaciones,
        )


def insertar_distribucion_valoraciones_gpu(conn, data_distribuciones):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO distribucion_valoraciones (
                producto_id,
                estrellas_5,
                estrellas_4,
                estrellas_3,
                estrellas_2,
                estrellas_1,
                fuente_desglose
            )
            VALUES (
                %(producto_id)s,
                %(estrellas_5)s,
                %(estrellas_4)s,
                %(estrellas_3)s,
                %(estrellas_2)s,
                %(estrellas_1)s,
                %(fuente_desglose)s
            );
            """,
            data_distribuciones,
        )
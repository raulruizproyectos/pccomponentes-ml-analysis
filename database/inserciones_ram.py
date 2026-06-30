# Inserciones de datos limpios de RAM en PostgreSQL.


def insertar_distribucion_valoraciones(conn, data_distribuciones):
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


def insertar_productos_ram(conn, data_productos):
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


def insertar_especificaciones_ram(conn, data_especificaciones):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO especificaciones_ram (
                producto_id,
                tipo_memoria,
                capacidad_gb,
                kit,
                num_modulos,
                capacidad_por_modulo_gb,
                frecuencia_mhz,
                latencia_cl,
                voltaje,
                diseno,
                compatibilidad,
                color,
                disipador,
                fuente
            )
            VALUES (
                %(producto_id)s,
                %(tipo_memoria)s,
                %(capacidad_gb)s,
                %(kit)s,
                %(num_modulos)s,
                %(capacidad_por_modulo_gb)s,
                %(frecuencia_mhz)s,
                %(latencia_cl)s,
                %(voltaje)s,
                %(diseno)s,
                %(compatibilidad)s,
                %(color)s,
                %(disipador)s,
                %(fuente)s
            );
            """,
            data_especificaciones,
        )


def insertar_resenas_ram(conn, data_resenas):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO resenas (
                resena_id,
                producto_id,
                valoracion,
                fecha_resena_texto,
                variante_modelo,
                texto_resena,
                pros,
                contras,
                likes,
                numero_respuestas
            )
            VALUES (
                %(resena_id)s,
                %(producto_id)s,
                %(valoracion)s,
                %(fecha_resena_texto)s,
                %(variante_modelo)s,
                %(texto_resena)s,
                %(pros)s,
                %(contras)s,
                %(likes)s,
                %(numero_respuestas)s
            );
            """,
            data_resenas,
        )

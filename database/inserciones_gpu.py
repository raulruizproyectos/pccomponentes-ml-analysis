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
            )
            ON CONFLICT (producto_id) DO UPDATE SET
                nombre = EXCLUDED.nombre,
                sku = EXCLUDED.sku,
                marca = EXCLUDED.marca,
                precio = EXCLUDED.precio,
                moneda = EXCLUDED.moneda,
                valoracion_media = EXCLUDED.valoracion_media,
                total_opiniones = EXCLUDED.total_opiniones,
                total_resenas_con_texto = EXCLUDED.total_resenas_con_texto,
                porcentaje_recomendacion = EXCLUDED.porcentaje_recomendacion,
                numero_recomendaciones = EXCLUDED.numero_recomendaciones,
                pagina_origen = EXCLUDED.pagina_origen,
                posicion_listado = EXCLUDED.posicion_listado,
                presente_en_detalle = EXCLUDED.presente_en_detalle,
                fuente = EXCLUDED.fuente;
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
            )
            ON CONFLICT (producto_id) DO UPDATE SET
                gpu = EXCLUDED.gpu,
                memoria_vram = EXCLUDED.memoria_vram,
                tipo_memoria = EXCLUDED.tipo_memoria,
                bus_memoria = EXCLUDED.bus_memoria,
                ancho_banda_memoria = EXCLUDED.ancho_banda_memoria,
                velocidad_memoria = EXCLUDED.velocidad_memoria,
                reloj_base = EXCLUDED.reloj_base,
                reloj_boost = EXCLUDED.reloj_boost,
                salidas_video = EXCLUDED.salidas_video,
                resolucion_maxima = EXCLUDED.resolucion_maxima;
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
            )
            ON CONFLICT (producto_id) DO UPDATE SET
                estrellas_5 = EXCLUDED.estrellas_5,
                estrellas_4 = EXCLUDED.estrellas_4,
                estrellas_3 = EXCLUDED.estrellas_3,
                estrellas_2 = EXCLUDED.estrellas_2,
                estrellas_1 = EXCLUDED.estrellas_1,
                fuente_desglose = EXCLUDED.fuente_desglose;
            """,
            data_distribuciones,
        )


def insertar_resenas_gpu(conn, data_resenas):
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO resenas_gpu (
                resena_id,
                producto_id,
                fecha_resena_texto,
                texto_resena,
                pros,
                contras
            )
            VALUES (
                %(resena_id)s,
                %(producto_id)s,
                %(fecha_resena_texto)s,
                %(texto_resena)s,
                %(pros)s,
                %(contras)s
            )
            ON CONFLICT (resena_id) DO UPDATE SET
                fecha_resena_texto = EXCLUDED.fecha_resena_texto,
                texto_resena = EXCLUDED.texto_resena,
                pros = EXCLUDED.pros,
                contras = EXCLUDED.contras;
            """,
            data_resenas,
        )

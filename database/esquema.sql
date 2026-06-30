-- Esquema PostgreSQL del proyecto pccomponentes_ml.
-- Adaptado a los datos limpios actuales de RAM extraídos desde PcComponentes.

CREATE TABLE IF NOT EXISTS productos (
    producto_id VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(300) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    sku VARCHAR(100) NOT NULL,
    marca VARCHAR(100),
    categoria VARCHAR(30) NOT NULL,
    precio NUMERIC(10, 2) NOT NULL,
    moneda VARCHAR(10) NOT NULL DEFAULT 'EUR',
    valoracion_media NUMERIC(4, 2),
    total_opiniones INT NOT NULL DEFAULT 0,
    total_resenas_con_texto INT,
    porcentaje_recomendacion NUMERIC(5, 2),
    numero_recomendaciones INT,
    pagina_origen INT NOT NULL,
    posicion_listado INT NOT NULL,
    presente_en_detalle BOOLEAN NOT NULL,
    fuente VARCHAR(100) NOT NULL,
    CONSTRAINT productos_categoria_valida
        CHECK (categoria IN ('tarjeta_grafica', 'memoria_ram'))
);

CREATE TABLE IF NOT EXISTS especificaciones_ram (
    producto_id VARCHAR(30) PRIMARY KEY
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    tipo_memoria VARCHAR(50),
    capacidad_gb NUMERIC(8, 2),
    kit VARCHAR(100),
    num_modulos INT,
    capacidad_por_modulo_gb NUMERIC(8, 2),
    frecuencia_mhz INT,
    latencia_cl INT,
    voltaje NUMERIC(4, 2),
    diseno TEXT,
    compatibilidad TEXT,
    color VARCHAR(100),
    disipador BOOLEAN,
    fuente VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS distribucion_valoraciones (
    producto_id VARCHAR(30) PRIMARY KEY
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    estrellas_5 INT NOT NULL DEFAULT 0,
    estrellas_4 INT NOT NULL DEFAULT 0,
    estrellas_3 INT NOT NULL DEFAULT 0,
    estrellas_2 INT NOT NULL DEFAULT 0,
    estrellas_1 INT NOT NULL DEFAULT 0,
    fuente_desglose VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS resenas (
    resena_id VARCHAR(50) PRIMARY KEY,
    producto_id VARCHAR(30) NOT NULL
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    valoracion NUMERIC(3, 1) NOT NULL,
    fecha_resena_texto TEXT NOT NULL,
    variante_modelo VARCHAR(150),
    texto_resena TEXT NOT NULL,
    pros TEXT,
    contras TEXT,
    likes INT,
    numero_respuestas INT
);

CREATE TABLE IF NOT EXISTS especificaciones_gpu (
    producto_id VARCHAR(30) PRIMARY KEY
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    gpu VARCHAR(150),
    memoria_vram VARCHAR(50),
    tipo_memoria VARCHAR(50),
    bus_memoria VARCHAR(50),
    ancho_banda_memoria VARCHAR(100),
    velocidad_memoria VARCHAR(100),
    reloj_base VARCHAR(100),
    reloj_boost VARCHAR(100),
    salidas_video TEXT,
    resolucion_maxima VARCHAR(100)
);

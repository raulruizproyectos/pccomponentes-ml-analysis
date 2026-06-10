-- Esquema PostgreSQL del proyecto pccomponentes_ml.
-- Este archivo permite recrear la estructura validada de la base de datos.

CREATE TABLE IF NOT EXISTS productos (
    producto_id SERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    modelo VARCHAR(300) NOT NULL,
    marca VARCHAR(100),
    precio NUMERIC(10, 2),
    valoracion_media NUMERIC(3, 2),
    numero_total_opiniones INT,
    porcentaje_recomendacion NUMERIC(5, 2),
    numero_recomendaciones INT,
    CONSTRAINT productos_categoria_valida
        CHECK (categoria IN ('tarjeta_grafica', 'memoria_ram'))
);

CREATE TABLE IF NOT EXISTS especificaciones_gpu (
    especificacion_id SERIAL PRIMARY KEY,
    producto_id INT UNIQUE NOT NULL
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

CREATE TABLE IF NOT EXISTS especificaciones_ram (
    especificacion_ram_id SERIAL PRIMARY KEY,
    producto_id INT UNIQUE NOT NULL
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    memoria_interna VARCHAR(50),
    diseno_memoria VARCHAR(100),
    tipo_memoria VARCHAR(50),
    velocidad_frecuencia VARCHAR(100),
    voltaje VARCHAR(50),
    compatibilidad TEXT
);

CREATE TABLE IF NOT EXISTS distribucion_valoraciones (
    producto_id INT PRIMARY KEY
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    estrellas_5 INT DEFAULT 0,
    estrellas_4 INT DEFAULT 0,
    estrellas_3 INT DEFAULT 0,
    estrellas_2 INT DEFAULT 0,
    estrellas_1 INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resenas (
    resena_id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL
        REFERENCES productos(producto_id)
        ON DELETE CASCADE,
    usuario VARCHAR(150),
    valoracion NUMERIC(3, 1),
    texto_resena TEXT,
    pros TEXT,
    contras TEXT
);

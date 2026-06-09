# Fuentes de datos - Memorias RAM PcComponentes

## Objetivo

Analizar de donde vamos a extraer los datos de memorias RAM antes de programar el scraper.

Fecha de consulta manual: 9 de junio de 2026.

Convencion: cuando PcComponentes no muestra un dato, se registra como `NULL`. Al preparar los datos en Python se utilizara `None`.

## Campos a extraer

| Campo | Ejemplo | Fuente en la pagina | Dificultad | Notas |
|---|---|---|---|---|
| modelo | Kingston FURY Beast DDR5 5200MHz 16GB CL40 | titulo del producto | baja | suele contener capacidad, tipo y frecuencia |
| marca | Kingston | titulo/ficha tecnica | baja | puede estar incluida en el modelo |
| precio | 209.95 | ficha/listado | baja/media | es un dato variable y debe guardarse con fecha |
| memoria interna | 16 GB | titulo/especificaciones | media | capacidad total del producto |
| diseno de memoria | 1 x 16 GB | titulo/especificaciones | media | numero de modulos y capacidad por modulo |
| tipo de memoria | DDR5 | titulo/especificaciones | media | por ejemplo DDR4 o DDR5 |
| velocidad/frecuencia | 5200 MHz | titulo/especificaciones | media | puede aparecer en MHz o MT/s |
| voltaje | 1.1 V | especificaciones | media/alta | no siempre aparece en la ficha |
| compatibilidad | Intel XMP 3.0 | descripcion/especificaciones | media/alta | perfiles y plataformas compatibles |
| valoracion | 4.6/5 | ficha del producto | baja/media | la valoracion individual puede no estar visible |
| resenas | texto de usuarios | seccion de opiniones | alta | puede tener paginacion o texto recortado |

## Productos analizados manualmente

### Producto 1

URL: https://www.pccomponentes.com/memoria-ram-forgeon-cyclone-pro-ddr5-6000-mhz-32-gb-2x16gb-cl30-negra

P/N: FO-DDR5-PRO-32GBCL30

Modelo detectado: Forgeon Cyclone PRO DDR5 6000 MHz 32 GB 2x16GB CL30 Negra

Marca detectada: Forgeon

Precio detectado: 469,95 EUR

Memoria interna detectada: 32 GB

Diseno de memoria detectado: 2 x 16 GB

Tipo de memoria detectado: DDR5

Velocidad/frecuencia detectada: 6000 MHz

Voltaje detectado: NULL

Compatibilidad detectada: Intel XMP y AMD Ryzen

Valoracion media detectada: 4,7/5

Numero total de opiniones: 108

Porcentaje que recomiendan: 74%

Numero de recomendaciones: 58

Distribucion de valoraciones:

- 5 estrellas: 96
- 4 estrellas: 6
- 3 estrellas: 2
- 2 estrellas: 1
- 1 estrella: 3

Notas:

- El precio, las opiniones y las recomendaciones pueden cambiar.
- PcComponentes no muestra el voltaje en el texto accesible de la ficha.
- No se utilizaran fuentes externas para completar campos ausentes.

## Resenas individuales analizadas manualmente - Producto 1

### Resena individual 1

Usuario: NIB

Valoracion: NULL

Texto resumido:

Compro un segundo kit para ampliar a 64 GB. Destaca el acabado y la gestion termica, pero encontro inestabilidad al usar cuatro modulos a 6000 MHz con XMP.

Pros:

- Buen acabado.
- Buena gestion termica.

Contras:

- Precio elevado.
- Posible inestabilidad con cuatro modulos a 6000 MHz.

### Resena individual 2

Usuario: Ayo10

Valoracion: NULL

Texto resumido:

Esta satisfecho con el kit DDR5 de 32 GB a 6000 MHz y CL30. Lo eligio por sus prestaciones y por las opiniones positivas de la marca.

Pros:

- DDR5 a 6000 MHz.
- Kit de 32 GB con latencia CL30.

Contras:

- Sobreprecio general de la memoria RAM.

### Resena individual 3

Usuario: LuALoCor

Valoracion: NULL

Texto resumido:

El primer kit funciono correctamente en dual channel y decidio comprar otro. Considera positiva la relacion entre precio y calidad.

Pros:

- Buena relacion calidad/precio.
- Buen funcionamiento en dual channel.

Contras:

- El comportamiento a largo plazo esta por comprobar.

### Producto 2

URL: https://www.pccomponentes.com/kingston-fury-beast-ddr5-5200mhz-16gb-cl40

P/N: KF552C40BB-16

Modelo detectado: Kingston FURY Beast DDR5 5200MHz 16GB CL40

Marca detectada: Kingston

Precio detectado: 209,95 EUR

Memoria interna detectada: 16 GB

Diseno de memoria detectado: 1 x 16 GB

Tipo de memoria detectado: DDR5

Velocidad/frecuencia detectada: 5200 MHz

Voltaje detectado: 1,1 V

Compatibilidad detectada: Intel XMP 3.0 y plataformas compatibles con DDR5 DIMM de 288 pines

Valoracion media detectada: 4,6/5

Numero total de opiniones: 187

Porcentaje que recomiendan: 95%

Numero de recomendaciones: 137

Distribucion de valoraciones:

- 5 estrellas: 151
- 4 estrellas: 28
- 3 estrellas: 4
- 2 estrellas: 1
- 1 estrella: 3

Notas:

- El titulo, el P/N y las opiniones indican que es un unico modulo de 16 GB.
- La ficha contiene una linea inconsistente que indica dos modulos de 16 GB.
- Para la base de datos se usara `1 x 16 GB`, pendiente de una verificacion adicional si cambia la ficha.

## Resenas individuales analizadas manualmente - Producto 2

### Resena individual 1

Usuario: EJCF

Valoracion: NULL

Texto resumido:

Eligio inicialmente un modulo de 16 GB para poder ampliar el equipo mas adelante. Valora el disipador sin iluminacion y su integracion en un equipo gris y negro.

Pros:

- Capacidad suficiente para comenzar.
- Permite ampliar con mas modulos.
- Disipador sin iluminacion.

Contras:

- Precio elevado de DDR5.

### Resena individual 2

Usuario: RAR

Valoracion: NULL

Texto resumido:

Destaca el rendimiento y la relacion calidad/precio con un equipo AMD. Recibio inicialmente un modulo defectuoso, pero la sustitucion fue rapida.

Pros:

- Buen rendimiento.
- Buena relacion calidad/precio.

Contras:

- El primer modulo recibido estaba defectuoso.

### Resena individual 3

Usuario: RedCat

Valoracion: NULL

Texto resumido:

Considera que los materiales son de calidad y que el modulo funciona correctamente con perfiles XMP o EXPO en un sistema AMD.

Pros:

- Materiales de calidad.
- Buen rendimiento.
- Compatible con perfiles de memoria.

Contras:

- Precio.

### Producto 3

URL: https://www.pccomponentes.com/kingston-so-dimm-ddr4-3200mhz-16gb-cl22

P/N: KCP432SS8/16

Modelo detectado: Kingston SO-DIMM DDR4 3200MHz 16GB CL22

Marca detectada: Kingston

Precio detectado: 129,95 EUR

Memoria interna detectada: 16 GB

Diseno de memoria detectado: 1 x 16 GB

Tipo de memoria detectado: DDR4

Velocidad/frecuencia detectada: 3200 MHz

Voltaje detectado: 1,2 V

Compatibilidad detectada: ordenadores portatiles y mini PC compatibles con DDR4 SO-DIMM de 260 pines a 3200 MHz

Valoracion media detectada: 4,9/5

Numero total de opiniones: 7

Porcentaje que recomiendan: 100%

Numero de recomendaciones: 6

Distribucion de valoraciones:

- 5 estrellas: 7
- 4 estrellas: 0
- 3 estrellas: 0
- 2 estrellas: 0
- 1 estrella: 0

## Resenas individuales analizadas manualmente - Producto 3

### Resena individual 1

Usuario: merlin1300

Valoracion: NULL

Texto resumido:

La recomienda para ampliar un portatil o mini PC. La instalacion fue sencilla, el equipo la reconocio correctamente y noto mayor fluidez al trabajar con varias aplicaciones.

Pros:

- Facil de instalar.
- Reconocimiento inmediato.
- Mejora el rendimiento en multitarea.
- Buena relacion calidad/precio.

Contras:

- La latencia CL22 no esta orientada a equipos de gaming extremo.
- Es necesario comprobar la compatibilidad del equipo.

### Resena individual 2

Usuario: JUANCARLOSR

Valoracion: NULL

Texto resumido:

El modulo cumple su funcion, encaja correctamente en el espacio disponible y funciona sin problemas.

Pros:

- Adaptacion correcta al espacio disponible.

Contras:

- El precio ha subido.

### Resena individual 3

Usuario: BerB

Valoracion: NULL

Texto resumido:

El portatil detecto la memoria inmediatamente y el modulo funciona correctamente junto a la memoria que ya tenia instalada.

Pros:

- Buena compatibilidad.
- Deteccion inmediata.

Contras:

- Ninguno detectado hasta el momento.

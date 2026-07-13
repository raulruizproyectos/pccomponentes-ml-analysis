# Estado de la entrega

Esta lista sigue los criterios de `enunciado.md`.

## Fase 01: infraestructura y datos

- [x] Scraping de memorias RAM.
- [x] Datos de tarjetas gráficas incorporados y adaptados.
- [x] Limpieza de productos, especificaciones y reseñas.
- [x] Archivos JSON brutos y procesados.
- [x] Esquema PostgreSQL para RAM y GPU.
- [x] Base de datos RDS poblada.
- [x] Bucket S3 configurado.
- [x] Lambda ETL conectada con S3 y RDS.
- [x] Lambda conectada a la VPC y RDS cerrado al acceso público general.
- [x] Disparadores separados para RAM y GPU.
- [x] Prueba controlada S3 -> Lambda -> RDS para ambas categorías.
- [x] Configurar la ejecución periódica del scraping (desactivada por defecto para evitar consumo recurrente en AWS).

## Fase 02: modelos y aplicación

- [x] EDA de RAM y GPU.
- [x] Clustering de RAM y GPU.
- [x] Análisis de sentimiento de RAM y GPU.
- [x] Resultados de modelos guardados en PostgreSQL.
- [x] Endpoint `/ask`.
- [x] Endpoint `/similar-products`.
- [x] Endpoint `/sentiment`.
- [x] Endpoint `/modelos/pca`.
- [x] Streamlit conectado con FastAPI.
- [x] Asistente de preguntas.
- [x] Análisis por producto.
- [x] Recomendador real del mismo clúster.
- [x] Mapa interactivo PCA.
- [x] Desplegar FastAPI en EC2.

## Preparación de la entrega

- [x] Plantilla `.env.example` sin secretos.
- [x] Comprobaciones de Streamlit, PCA y Lambda.
- [x] Comprobación automática de endpoints.
- [x] Guía de evaluación en README.
- [x] Añadir la URL pública de EC2 al README.
- [x] Ejecutar la prueba final desde una copia limpia.
- [x] Preparar la demostración final del flujo completo.

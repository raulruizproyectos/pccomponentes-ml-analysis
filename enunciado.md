# Propuesta de Proyecto: Pipeline y API de Clustering y Análisis de Reseñas con PcComponentes

## 👥 Roles y Responsabilidades

### 🏗️ Data Architect

* **Responsable del Diseño en AWS:**
    - Definir y configurar la arquitectura en la nube, incluyendo el bucket S3, la base de datos **PostgreSQL en RDS** y los permisos de los servicios.

### ⚙️ Data Engineer

* **Responsable del Pipeline de Datos:**
    - Implementar los scripts de **web scraping** (usando herramientas como requests o httpx) para la extracción masiva de catálogos de productos, especificaciones técnicas y, fundamentalmente, el histórico de **reseñas y valoraciones** de usuarios en PcComponentes.
    - Gestionar la limpieza del texto (eliminación de etiquetas HTML, caracteres especiales), transformación y carga de estos datos desde S3 a la base de datos.

### 🔬 Data Scientist

* **Responsable del Análisis y Modelado:**
    - Aplicar técnicas de Procesamiento de Lenguaje Natural (NLP) para analizar el sentimiento y extraer los temas principales de las reseñas de los usuarios (ej. qué opinan de la batería, el rendimiento o la pantalla).
    - Entrenar un modelo de **clustering** (aprendizaje no supervisado, como K-Means o DBSCAN) para agrupar productos con características técnicas similares y patrones de satisfacción de usuario parecidos.
    - Diseñar la lógica para interpretar las preguntas en lenguaje natural del endpoint de Q&A.

### 🚀 ML Engineer

* **Responsable del Despliegue y la API:**
    - Envolver la lógica de consulta, los resultados del clustering y el análisis de sentimiento en una API robusta utilizando FastAPI.
    - Desplegar la aplicación FastAPI en una instancia de AWS EC2, asegurando que los endpoints sean escalables y rápidos.

---

## 📝 Fases del Proyecto

### **Fase 01: Infraestructura y Pipeline de Datos (Web Scraping)**

**Objetivo:** Construir un sistema automatizado que extraiga el catálogo de productos y las reseñas de usuarios de PcComponentes mediante web scraping, almacenándolos de forma estructurada para su posterior análisis.

**Tareas Clave:**

1. **Extracción de Datos (Data Engineer, Architect):**
    - Desarrollar la lógica de scraping para navegar por las categorías de hardware.
    - Crear un pipeline para extraer metadatos del producto (precio, marca, especificaciones) y todo el texto de las reseñas de los compradores, guardando los JSON extraídos en un **bucket S3**.
    - Configurar un proceso recurrente para que se ejecute de forma semanal o diaria, capturando nuevos productos y reseñas recientes.

2. **Procesamiento y Carga (Data Engineer, Architect):**
    - Desarrollar una **AWS Lambda** que se active con un **trigger de S3** al recibir los nuevos ficheros del scraping.
    - Esta función normalizará las especificaciones técnicas (ej. estandarizar la memoria RAM a GB), limpiará el texto de las reseñas para el análisis NLP y cargará todo en la base de datos **PostgreSQL**.

3. **Exploratory Data Analysis (EDA) Preliminar (Data Scientist)**:
    - Conectarse a PostgreSQL usando Jupyter Notebooks para analizar la distribución de valoraciones (estrellas) frente al precio de los componentes.
    - Realizar análisis de frecuencia sobre las reseñas para identificar los términos más comunes positivos y negativos.
    - Identificar las características técnicas más relevantes para definir los *features* que se usarán en el algoritmo de clustering.

**Entregables de esta fase:**

* Infraestructura en AWS (S3, RDS, contenedores para scraping) configurada y tolerante a bloqueos.
* Pipelines automáticos de web scraping de productos y opiniones funcionando.
* Base de datos poblada, estructurada y limpia con el ecosistema de PcComponentes.

### **Fase 02: Modelado, API y Despliegue**

**Objetivo:** Desarrollar una API que permita entender qué opinan los usuarios sobre los componentes y descubrir grupos de productos similares que ofrezcan un valor equivalente en el mercado.

**Tareas Clave:**

1. **Desarrollo de Modelos (Data Scientist):**
    - **Clustering:** Entrenar un modelo que agrupe componentes (ej. tarjetas gráficas o portátiles) basándose en sus especificaciones técnicas, precio y score de sentimiento, permitiendo descubrir alternativas de compra ("productos del mismo clúster").
    - **NLP:** Aplicar modelos de *Sentiment Analysis* sobre el texto de las reseñas para clasificar opiniones y extraer pros y contras automáticamente.

2. **Desarrollo de la API (ML Engineer, Data Scientist):**
    - Crear una aplicación con **FastAPI** que incluya los siguientes endpoints:
        - `/ask`: Recibe una pregunta en texto (ej. *"¿Cuáles son las quejas más comunes sobre este monitor?"*), busca en las reseñas procesadas y devuelve un resumen.
        - `/similar-products`: Recibe el ID de un producto y devuelve componentes que pertenezcan a su mismo clúster, ordenados por mejor sentimiento de usuario.
        - `/sentiment`: Devuelve un desglose del análisis de reseñas de un producto específico (% positivo, neutral, negativo y palabras clave).

3. **Despliegue (ML Engineer):**
    - Desplegar la aplicación FastAPI completa en una instancia **AWS EC2** para que sea consumible por el frontend.


4. **Desarrollo de la Interfaz Web interactiva (Data Scientist, ML Engineer)**:
    - **Dashboard Analítico**: Construir una aplicación en Streamlit que muestre un mapa interactivo (usando reducciones de dimensionalidad como PCA) donde el usuario pueda explorar visualmente los **clústeres de productos**.
    - **Integración de la API**:
        - Asistente de Compras: Integrar una barra de búsqueda donde el usuario pueda hacer preguntas en lenguaje natural sobre dudas específicas del catálogo (ej. "¿Cuáles son las quejas más comunes sobre este monitor?" o "¿Qué dice la gente sobre la temperatura de esta tarjeta gráfica?"), obteniendo respuestas directas consumiendo el endpoint `/ask`.
        - Panel de análisis de un producto concreto: al seleccionar un componente, la web consumirá `/sentiment` para mostrar gráficos de pastel con la opinión general y las palabras clave de las reseñas.
        - Recomendador basado en clustering: un buscador donde introduces un producto que quieres comprar, y el sistema te recomienda alternativas viables de su mismo clúster consumiendo `/similar-products`.

**Entregables de esta fase:**

- Modelos de clustering y NLP entrenados e integrados.
- API funcional desplegada con los tres endpoints implementados y documentados.
- Dashboard interactivo en Streamlit donde el usuario pueda explorar los clústeres de componentes y analizar fácilmente el sentimiento de reseñas.

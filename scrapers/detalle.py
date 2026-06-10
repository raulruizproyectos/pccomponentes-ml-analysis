"""
Scraper de DETALLE (ficha) de tarjetas gráficas (PENDIENTE).

Plantilla de referencia: `detalle_ram.py`.

Características que ya están resueltas en la versión de RAM y que
deberíamos reutilizar:
    - Reanudación robusta por URL (no por ID, porque los IDs cambiaron
      de formato ram_001 → ram_0001).
    - Checkpoints periódicos + guardado de errores.
    - Manejo elegante de BloqueoDetectadoError (SystemExit(2)) para bloqueos reales.
    - Productos sin datos (sin Product JSON-LD ni opiniones) se saltan
      (error recuperable, no paran el scraper).
    - Extracción de opiniones (resumen + lista de reseñas desde JSON-LD).
    - Llamadas a funciones de utilidades.py (obtener_html con validación,
      combinar_resumen_opiniones, extraer_resenas..., etc.).

Tareas típicas para la versión GPU:
    - Extraer modelo, VRAM, GPU, bus, relojes, salidas, resolución máx.
    - (Opcional) Parser de especificaciones más rico que el de RAM.
"""

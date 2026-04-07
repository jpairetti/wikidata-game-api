Este documento define los conceptos técnicos fundamentales utilizados en el desarrollo de la API de recomendación de videojuegos.

---

### Arquitectura y Protocolos
* **API REST:** Estilo de arquitectura para sistemas distribuidos basado en HTTP. Se caracteriza por no tener estado, lo que significa que cada petición debe contener toda la información necesaria para ser procesada.
* **Endpoint:** URL (ruta) que expone una operación de la API; típicamente un método HTTP sobre un path (ej. `GET /usuarios`).
* **Recurso:** Cualquier entidad o dato gestionado por la API (usuarios, juegos, sugerencias). Cada recurso tiene un identificador único.
* **Contrato de API:** especificación (aquí, OpenAPI) que define métodos, rutas, cuerpos y respuestas esperadas.
* **Idempotencia:** Propiedad de algunos métodos HTTP (GET, PUT, DELETE) donde el resultado de realizar una petición varias veces es el mismo que realizarla una sola vez.
* **Proxy (en este lab):** nuestra API actúa como cliente frente a Wikidata y como servidor frente al usuario; ante fallos de la API externa devolvemos 502 (Bad Gateway).

### Seguridad y Autenticación
* **Hashing:** Proceso algorítmico irreversible que transforma una contraseña en una cadena de caracteres fija para su almacenamiento seguro.
* **Token de Sesión:** Identificador único generado tras un login exitoso. Permite al servidor reconocer al usuario en peticiones posteriores sin pedir la contraseña nuevamente.
* **Timeout:** Límite de tiempo que un cliente o servidor espera para completar una operación de red antes de darla por fallida.
* **Variables de Entorno:** Parámetros configurables externos al código (como el puerto o la ruta de la DB) que permiten adaptar la app a distintos entornos sin modificar archivos fuentes.

### Calidad de Software
* **Docker:** Tecnología que empaqueta la aplicación y sus dependencias (Python, librerías, etc.) para asegurar que funcione idénticamente en cualquier sistema operativo.
* **Health Check:** Endpoint (`/health`) diseñado para que herramientas de monitoreo verifiquen si el servicio está activo y respondiendo correctamente.
* **Linters:** Herramientas de análisis estático que revisan el código en busca de errores de estilo o posibles bugs sin ejecutarlo (ej: `Pylint, Flake8, Black`).
* **Cobertura de Tests:** porcentaje de líneas del código en `src/` que son ejecutadas por los tests.
* **Complejidad Ciclomática:** Medida de la complejidad lógica de una función basada en el número de caminos posibles (if/else, loops). Una complejidad baja facilita el mantenimiento y el testeo.
* **Logging mínimo por request:** la API debe escribir al menos, por cada request, el método, path, código de respuesta y tiempo de respuesta (ms)
---
*Famaf - Redes y Sistemas Distribuidos 2026 - Grupo 31 - Integrantes: Lissandro Bosque, Franco Galassi, Joaquin Pairetti*
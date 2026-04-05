# Recomendador de Videojuegos — Laboratorio 1 (2026)

Proyecto base para implementar la API según el contrato en `openapi.yaml`. El archivo **openapi.yaml** define los endpoints; las rutas están registradas en **app.py** y la lógica de cada una se implementa en los módulos de **src/** (usuarios, juegos, sugerencias, wikidata, filtros).

## Requisitos

- **Docker (recomendado)** para ejecutar la API y el grading sin instalar Python localmente.
- Alternativa: Python 3.10 o superior, venv y `pip install -r requirements.txt`.

## Configuración y uso

### Con Docker (recomendado)

```bash
make docker-build
make docker-run
```

Con la API corriendo, abrí **http://localhost:5000/docs**. Para verificar tests, cobertura, lint y complejidad sin tener Python local:

```bash
make docker-grade
```

Necesitás un archivo `.env` en la raíz (copiá desde `.env.example`). Los datos se persisten en SQLite (por defecto `instance/datos.db`). Para volver a empezar con datos vacíos: `make clean-db`.

### Alternativa con venv

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Opcional: WIKIDATA_USER_AGENT para llamadas a Wikidata
make run
```
Si no usás make: `PYTHONPATH=. python3 -m src.app`.

- `make test` — Ejecuta los tests
- `make grade` — Ejecuta el script de grading (tests + cobertura + lint + complejidad)
- `make lint` — Ruff y radon
- `make clean-db` — Borra la base SQLite para empezar de cero con datos vacíos

Los tests en **test_metrics.py** comprueban estilo (ruff) y complejidad ciclomática; si fallan, corregir el código en **src/** (refactorizar funciones demasiado largas o con muchas ramas).
Este proyecto consiste en una API REST desarrollada con **Flask** para la cátedra de Redes y Sistemas Distribuidos (FaMAF, 2026). La aplicación permite gestionar usuarios, sus colecciones personales de videojuegos y obtener recomendaciones basadas en datos de **Wikidata**.

---

## Estructura del Proyecto

El código se organiza de forma modular para separar las responsabilidades de la API:

* **`app.py`**: Punto de entrada de la aplicación. Configura el servidor Flask, registra las rutas y sirve la documentación.
* **`auth.py`**: Gestiona la seguridad. Incluye el registro, el login y la lógica de generación/validación de tokens (UUID4) y hashing de contraseñas.
* **`usuarios.py`**: Implementa el CRUD.
* **`juegos.py`**: Controla las colecciones personales (agregar, listar, editar o eliminar juegos de la lista de un usuario).
* **`wikidata.py`**: Cliente que interactúa con la API externa de Wikidata para buscar información de videojuegos globales.
* **`sugerencias.py`**: Lógica de recomendación basada en los géneros y juegos de la colección del usuario.
* **`store.py`**: Capa de persistencia que interactúa con la base de datos SQLite.

## Metodologia de trabajo

Nos dividimos el trabajo asignando modulos para implementar a cada integrante, aunque en definitiva todo el grupo colaboro activamente en todo el proyecto via grupo de WhatsApp

* **Franco Galassi**: 
    * **Desarrollo (feat):** Implementación de lógica en `juegos.py`, `wikidata.py` y `usuario.py`.
    * **Gestión:** Edición del video de presentación y gestión de la entrega parcial.
    * **Mantenimiento (fix):** Correcciones y optimización en `wikidata.py`.

* **Lissandro Bosque**: 
    * **Desarrollo (feat):** Implementación del algoritmo en `sugerencia.py`, y lógica en `juegos.py` y `usuario.py`.
    * **Gestión:** Colaboración en la entrega parcial.

* **Joaquín Pairetti**: 
    * **Desarrollo (feat):** Implementación del sistema de autenticación en `auth.py`, integración con `wikidata.py`, creación de `test_privados` y redacción del `README.md`.
    * **Mantenimiento (fix):** Correcciones en los módulos de `juegos.py` y `wikidata.py`.

## decisiones de diseno y dificultades
1. Lógica de Validación y Tipado
Funciones de Parseo Centralizadas: Se implementaron funciones específicas para "limpiar" y validar los bodies de los Requests antes de que lleguen a la lógica de negocio. Esto asegura que si un campo obligatorio (como nombre en el registro) falta, la función retorne un error temprano, evitando llamadas innecesarias a la base de datos.

    Manejo de Respuestas: Se decidió que todas las funciones de lógica retornen una estructura consistente (ej. (data, error)), lo que permite que el manejador de la ruta decida el código HTTP de forma limpia, separando la ejecución del resultado.

2. Implementación de la Comunicación Externa
Estrategia de Tolerancia a Fallos: Se implementó una lógica de "Fail-Fast" mediante el uso de Timeouts en las funciones que consumen APIs externas. Si Wikidata no responde en el tiempo estipulado, la función captura la excepción y activa un flujo de error controlado para evitar que el hilo del servidor se cuelgue.

3. Seguridad de la Función de Autenticación
Comparación Segura: Para el login, se evitó cualquier lógica de comparación manual de strings. Se delegó la verificación a funciones criptográficas (check_password_hash).

    Validación de Sesión: Se implementó una lógica de interceptación que verifica la validez y expiración del token antes de ejecutar cualquier función protegida, garantizando que el usuario_id esté disponible para las funciones subsiguientes.

4. Dificultades
En el transcurso del laboratorio, pudimos enfrentar bastantes dificultades generales, como el uso de un lenguaje al que estamos poco acostumbrados y la gestión de tiempos entre otras materias.
Hablando más específicamente del laboratorio, hubo funciones donde teníamos dudas de su comportamiento o teníamos poca noción de como empezar a trabajar en ellas. Hubo también algunos problemas para unirse al repositorio para comenzar a trabajar. También se daba el caso de obviar la lectura de documentación que terminaba causando confusión a la hora de programar por quedar con huecos en las bases de los temas. Por lo general, hablando de errores o desconocimiento, resolvimos las dudas con el uso de inteligencia artificial.


## Seguridad y Autenticación(de Flask)

El sistema implementa un esquema de autenticación basado en sesiones temporales y almacenamiento seguro de credenciales.

### 1. Hashing de Contraseñas
Para proteger la integridad de los datos, las contraseñas nunca se almacenan en texto plano. Si bien inicialmente se evaluó el uso de la librería bcrypt, se descartó esta opción al notar que la librería Werkzeug ya viene integrada con la instalación de Flask. De esta manera, evitamos incluir dependencias adicionales en el archivo requirements.txt. Aunque reconocemos que bcrypt ofrece una mayor resistencia ante ataques de fuerza bruta, para los fines de este proyecto priorizamos la consistencia del entorno y la legibilidad del código.

* **Registro:** Al crear un usuario, la contraseña se procesa con `generate_password_hash()`, que genera un hash único.
* **Login:** Durante la autenticación, se utiliza `check_password_hash()` para comparar de forma segura el hash almacenado en la base de datos con la contraseña proporcionada por el usuario.

### 2. Expiración de Tokens
La gestión de sesiones utiliza tokens únicos con un tiempo de vida limitado (TTL):

1. **Generación:** Al iniciar sesión exitosamente, se genera un token mediante `uuid4().hex`.
2. **Cálculo de Expiración:** Se establece una fecha límite sumando los minutos definidos en la configuración al tiempo actual en formato UTC (`datetime.now(timezone.utc)`).
3. **Persistencia:** El token y su fecha de expiración se guardan en la base de datos asociados al `usuario_id`.
4. **Validación:** En cada petición protegida, el sistema verifica:
    * Que el token exista en la base de datos.
    * Que el tiempo actual no haya superado el valor de `token_expira_en`.

### 3. Guía de Uso con `curl`

Para interactuar con la API desde la terminal, se pueden utilizar los siguientes comandos `curl`. 

#### Registrar un Nuevo Usuario

```bash
curl -X POST http://localhost:5000/auth/registro \
     -H "Content-Type: application/json" \
     -d '{
          "username": "tu_usuario",
          "nombre": "tu_nombre",
          "password": "tu_password"
         }'
```
#### Iniciar Sesión (Obtener Token)
Para autenticarse y recibir un token de sesión, realice un `POST` al endpoint de login:
```bash
curl -X POST http://localhost:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{
          "username": "tu_usuario",
          "password":
          "tu_password"
        }'
```
Para una exploración detallada de todos los endpoints, modelos de datos y pruebas en tiempo real, levantá el servidor y accedé a:
[http://localhost:5000/docs](http://localhost:5000/docs)

Desde allí podrás:
* **Visualizar** todos los métodos disponibles (GET, POST, PUT, DELETE).
* **Probar** los endpoints directamente desde el navegador (botón "Try it out").
* **Consultar** las estructuras de los JSON de entrada y salida

## Glosario

Para profundizar en los términos técnicos en este proyecto, consultá:

[**Glosario**](./GLOSARIO.md)
## Uso de IA en el proyecto
Durante el desarrollo del laboratorio, se utilizaron asistentes (específicamente Gemini y ChatGPT) como apoyo técnico.

1. Ámbitos de Aplicación
Debugging y Resolución de Errores: Se utilizó la IA para interpretar mensajes de error específicos de Flask y de los tests de la cátedra (ej. errores 400 Bad Request por falta de campos en el JSON o errores de conexión con la base de datos).

    Documentación (Markdown): El asistente fue fundamental para aplicar formato markdown, corregir errores ortograficos y de sintaxis en el README

    Explicación de Conceptos: Se utilizó para profundizar en términos teóricos como la idempotencia, la complejidad ciclomática y el funcionamiento del hashing de contraseñas. Tambien, la ia fue utilizada para conseguir fuentes directas donde consultar, ej.: Python (UUID/Datetime), Flask (Blueprints/Request context), Requests (Manejo de Timeouts) y Werkzeug (Security hashes). 

2. Metodología de Consulta
No se delegó la lógica de negocio completa a la IA, sino que se utilizó para resolver bloqueos puntuales (por ej,: funcion _obtener_labels) o mejorar la legibilidad del código (aplicacion de formato pep8).

3. Criterios de Revisión
Se verificó manualmente que cualquier sugerencia de código respetara los nombres de los campos y los códigos de estado HTTP (200, 201, 404, 502, etc.) definidos en el archivo openapi.yaml.

    Pruebas Locales: Ninguna función sugerida se integró definitivamente sin antes superar los tests públicos provistos y las pruebas manuales con curl.
##
*Famaf - Redes y Sistemas Distribuidos 2026 - Grupo 31 - Integrantes: Lissandro Bosque, Franco Galassi, Joaquin Pairetti*

# Video Game Backlog API

A REST API built with Flask for managing personal video game collections (backlog), with Wikidata integration for game data and token-based authentication.

---

## Overview

This API lets users maintain a personal video game list tagged with four status flags: `tengo` (own it), `quiero` (want it), `jugado` (played it), and `me_gusta` (like it). Game metadata is fetched from [Wikidata](https://www.wikidata.org/) on demand and cached locally in SQLite. A random suggestion endpoint lets users pick what to play next from games they own, optionally filtered by genre.

Built as Lab 1 for the Networks and Distributed Systems course at FAMAF (UNC), 2026. Group 31.

### Repository files

| File | Description |
|---|---|
| `openapi.yaml` | OpenAPI 3.0 contract — the authoritative definition of every endpoint, request/response schema, and status code. |
| `Informe.md` | Final project report (in Spanish) written for the course submission. Covers architecture, design decisions, team methodology, authentication design, and AI usage disclosure. |
| `enunciado.md` | Original lab assignment (in Spanish) provided by the course. Describes the phases, deliverables, and grading rubric. |
| `grade.py` | Grading script that runs tests, coverage, ruff, radon, and static auth checks. |
| `Makefile` | Convenience targets: `run`, `test`, `grade`, `lint`, `docker-*`, `clean-db`. |

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Service health check |
| GET | `/usuarios` | — | List all users |
| POST | `/usuarios` | — | Create a user |
| GET | `/usuarios/{id}` | — | Get user by ID |
| PUT | `/usuarios/{id}` | ✓ | Update user name |
| DELETE | `/usuarios/{id}` | ✓ | Delete user and their game list |
| GET | `/usuarios/{id}/juegos` | — | List user's games (filterable, sortable) |
| POST | `/usuarios/{id}/juegos` | ✓ | Add a game to the user's list |
| PUT | `/usuarios/{id}/juegos/{juego_id}` | ✓ | Update game flags |
| DELETE | `/usuarios/{id}/juegos/{juego_id}` | ✓ | Remove game from list |
| GET | `/usuarios/{id}/sugerencia` | — | Random suggestion from owned games |
| GET | `/juegos` | — | List catalog / search (local or Wikidata) |
| GET | `/juegos/{id}` | — | Get game by Wikidata Q-ID |
| POST | `/auth/registro` | — | Register a new account |
| POST | `/auth/login` | — | Log in, receive a token |

**Filters** on `GET /juegos`: `q` (search term), `fuente` (`local`\|`wikidata`), `genero`, `ordenar` (`nombre`\|`lanzamiento`\|`genero`\|`id`), `orden` (`asc`\|`desc`).

**Filters** on `GET /usuarios/{id}/juegos`: `genero`, `ordenar` (`nombre`\|`fecha_lanzamiento`\|`fecha_agregado`), `orden` (`asc`\|`desc`).

Interactive Swagger UI is served at `/docs` once the server is running.

---

## Wikidata Integration

Game data is fetched from the [Wikidata MediaWiki API](https://www.wikidata.org/w/api.php) using a multi-step pipeline in `src/wikidata.py`:

1. **Search** (`wbsearchentities`) — full-text search returns a list of Q-IDs.
2. **Filter** (`wbgetentities`, claims only) — each Q-ID is checked for `P31=Q7889` (instance of: video game) to discard non-game entities.
3. **Enrich** (`wbgetentities`, labels + descriptions + claims) — valid game IDs are fetched in full.
4. **Resolve labels** — the Q-IDs for genre and platform are resolved to human-readable labels in a single batched call.
5. **Map & cache** — results are mapped to the internal schema and persisted to `CATALOGO_JUEGOS` in SQLite, so future lookups skip Wikidata entirely.

**Claims mapped:**

| Property | Field | Notes |
|---|---|---|
| P31 (instance of) | — | Must equal Q7889 to be included |
| P577 (publication date) | `lanzamiento` | Formatted as YYYY-MM-DD |
| P136 (genre) | `genero` | Q-ID resolved to label |
| P400 (platform) | `plataforma` | Q-ID resolved to label |

**Timeout:** All Wikidata calls use a 10-second timeout (`WIKIDATA_TIMEOUT = 10`). Network errors, timeouts, and JSON parse failures are caught and returned as `None` by the internal `_request()` helper.

**502 vs 404:** When a Wikidata search fails entirely (upstream unavailable), the API returns `502 Bad Gateway` — we're acting as a proxy and the upstream isn't responding. When `GET /juegos/{id}` is called with a Q-ID that doesn't exist or isn't a video game, the API returns `404 Not Found`. Individual game lookups always return 404 on failure regardless of cause, since if an entity doesn't resolve we can't confirm whether it's a connectivity issue or a genuinely missing resource.

**User-Agent:** Configurable via `WIKIDATA_USER_AGENT` environment variable (default: `LabRedes2026/1.0`).

---

## Authentication

Authentication is implemented across `src/auth.py` (security logic) and `src/auth_common.py` (shared parsing and DB helpers).

### Password hashing

Passwords are never stored in plaintext. We use `werkzeug.security` — already bundled with Flask — rather than adding a separate `bcrypt` dependency:

- **Registration:** `generate_password_hash(password)` produces a salted hash stored in the `credenciales` table.
- **Login:** `check_password_hash(stored_hash, provided_password)` validates credentials without any direct string comparison.

We considered `bcrypt` (stronger against brute-force) but chose Werkzeug to keep the dependency footprint minimal and consistent with the Flask environment.

### Token lifecycle

1. On successful login, a token is generated via `uuid4().hex` (128-bit random opaque string).
2. An expiry timestamp is computed: `datetime.now(timezone.utc) + timedelta(minutes=TTL)`. Default TTL: 60 minutes; configurable via `AUTH_TOKEN_TTL_MINUTES`.
3. Token and expiry are written to the `credenciales` table (`token`, `token_expira_en` columns).
4. On every protected request, `obtener_usuario_actual()` parses `Authorization: Token <TOKEN>`, looks up the token in the DB, and validates expiry against current UTC time.

Protected endpoints use two decorators stacked in `app.py`: `requiere_auth` (validates the token) and `requiere_mismo_usuario` (verifies the token belongs to the user in the URL path).

### curl quick reference

**Register:**
```bash
curl -X POST http://localhost:5000/auth/registro \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "nombre": "Alice", "password": "secret"}'
```

**Login (get token):**
```bash
curl -X POST http://localhost:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "password": "secret"}'
# → {"token": "a1b2c3d4e5f6..."}
```

**Use the token:**
```bash
curl -X POST http://localhost:5000/usuarios/1/juegos \
     -H "Content-Type: application/json" \
     -H "Authorization: Token a1b2c3d4e5f6..." \
     -d '{"juego_id": "Q12395", "tengo": true, "quiero": false, "jugado": false, "me_gusta": false}'
```

---

## Design Decisions

**Single persistence layer (`store.py`):** All in-memory state (`USUARIOS`, `CATALOGO_JUEGOS`, `LISTAS_JUEGOS`) lives in one module. Every other module imports from it. SQLite writes are triggered explicitly by the caller after mutations (e.g., `_persist_listas()`) rather than auto-committed, keeping write paths visible and intentional.

**Shared filter module (`filtros.py`):** The same filter-and-sort logic applies to both a user's personal list (`juegos.py`) and the global catalog (`wikidata.py`). Extracting it into `filtros.py` avoids duplication and ensures consistent behavior. Each call site passes the appropriate `ordenes_validos` tuple to enforce context-specific sort fields.

**Structured return pattern:** Business logic functions return plain data or `None` — not HTTP responses — and the route handler decides the status code. This separates execution from presentation and makes the logic straightforward to unit-test.

**Fail-fast on external calls:** Wikidata calls use a 10-second timeout. Any `requests.RequestException` or JSON error is caught immediately in `_request()` and returned as `None`, preventing server threads from hanging on a slow upstream.

**`auth_common.py` as shared auth helpers:** Parsing, validation, and DB lookups shared between registration and login live in `auth_common.py`. `auth.py` handles only security-sensitive logic (hashing, token generation, expiry checking), keeping each module focused.

---

## Quality & Testing

Quality is enforced by a grading script (`grade.py`) with four blocking checks:

| Check | Tool | Threshold |
|---|---|---|
| Test coverage | pytest-cov | ≥ 70% of `src/` (we achieved 93%) |
| Code style | ruff | Zero errors |
| Cyclomatic complexity | radon | ≤ 8 per function |
| Auth security | static analysis | `generate_password_hash`, `check_password_hash`, and `token_expira_en` must be present |

Tests are organized into:
- `tests/test_public/` — course-provided contract tests (auth, users, games, Wikidata).
- `tests/test_private/` — our team's edge-case tests (game boundary conditions, genre-based suggestions).
- `tests/test_metrics.py` — style and complexity verification.

Run: `make grade` (local) or `make docker-grade` (Docker, no local Python needed).

---

## Team Methodology

Group 31 — 3 members. Work was divided by module with active collaboration throughout via a shared group chat.

- **Franco Galassi** — `juegos.py`, `wikidata.py`, `usuarios.py`; video editing and partial delivery management; Wikidata bug fixes.
- **Lissandro Bosque** — `sugerencias.py`, `juegos.py`, `usuarios.py`; partial delivery collaboration.
- **Joaquín Pairetti** — `auth.py`, Wikidata integration, `tests/test_private/`, README.

Development milestones tagged in git: `v0.1-parcial` (partial delivery checkpoint) and `entrega-final` (final submission).

---

## Glossary

| Term | Definition |
|---|---|
| **REST API** | Architectural style for distributed systems over HTTP. Stateless: each request carries all information needed to process it. |
| **Endpoint** | A URL + HTTP method pair exposing one operation (e.g., `GET /usuarios`). |
| **Resource** | Any entity managed by the API (users, games, suggestions). Each has a unique identifier. |
| **API Contract** | Specification (here, OpenAPI 3.0 in `openapi.yaml`) defining paths, methods, request/response shapes, and status codes. |
| **Idempotence** | Property of some HTTP methods (GET, PUT, DELETE) where repeating an identical request produces the same outcome as calling it once. |
| **Proxy** | Our API acts as a client to Wikidata and as a server to callers; when the upstream fails, we surface `502 Bad Gateway`. |
| **Password hashing** | One-way cryptographic transform of a password for secure storage. Direct string comparison is replaced by `check_password_hash`. |
| **Session token** | Opaque value generated at login and sent in `Authorization` headers to identify the user across requests without re-sending the password. |
| **Token TTL** | Time-to-live: the window (default 60 min) after which a token expires and the user must log in again. |
| **Timeout** | Maximum wait for a network call before treating it as failed. Wikidata calls use a 10-second timeout. |
| **Environment variable** | External configuration (port, DB path, TTL) that adapts the app to different environments without changing source code. |
| **Docker** | Containerization tool that packages the app with its dependencies for reproducible execution across machines. |
| **Health check** | `GET /health` returns `{"status": "ok"}`, used by Docker and monitoring infrastructure to verify the service is live. |
| **Linter** | Static analysis tool that checks code style without executing it. We use `ruff`. |
| **Test coverage** | Percentage of `src/` lines executed by the test suite. Required: ≥ 70%. |
| **Cyclomatic complexity** | Count of independent code paths through a function (branches, loops). Maximum allowed: 8 per function, measured with `radon`. |
| **Logging per request** | `app.py` records method, path, HTTP status, and response time (ms) for every request via `before_request`/`after_request` hooks. |

---

## AI Usage Disclosure

During development we used AI assistants (Gemini and ChatGPT) as technical support:

- **Debugging:** Interpreting Flask and pytest error messages (e.g., 400 responses from missing JSON fields, SQLite connection issues).
- **Documentation:** Markdown formatting, typo and syntax corrections in the README.
- **Concept clarification:** Idempotence, cyclomatic complexity, and password hashing mechanics. Also used to locate primary documentation: Python (UUID/datetime), Flask (Blueprints/request context), Requests (timeout handling), Werkzeug (security hashes).

We did not delegate business logic to AI. It was used to unblock specific sticking points (e.g., the `_obtener_labels` function) or to apply PEP 8 formatting. Every suggested snippet was verified against the field names and HTTP status codes in `openapi.yaml` and required passing the public test suite before being merged.

---

## Build & Run

### With Docker (recommended)

```bash
cp .env.example .env     # configure env vars if needed
make docker-build
make docker-run          # API at http://localhost:5000
```

Run tests and all quality checks without a local Python install:
```bash
make docker-grade
```

### Without Docker (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
make run                    # or: PYTHONPATH=. python3 -m src.app
```

| Command | Description |
|---|---|
| `make test` | Run the test suite |
| `make grade` | Tests + coverage + lint + complexity |
| `make lint` | ruff + radon |
| `make clean-db` | Delete the SQLite DB and start fresh |

Data is persisted at `instance/datos.db` (override with `LAB1_DATABASE`). Interactive docs: `http://localhost:5000/docs`.

---

## Course Context

**Lab 1 — Networks and Distributed Systems** (Redes y Sistemas Distribuidos), FAMAF — Universidad Nacional de Córdoba, 2026. Group 31.

*Lissandro Bosque · Franco Galassi · Joaquín Pairetti*

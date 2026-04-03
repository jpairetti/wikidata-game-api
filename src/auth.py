from __future__ import annotations

import os
from uuid import uuid4

from flask import jsonify, Response

from werkzeug.security import generate_password_hash, check_password_hash

from . import auth_common
from .store import guardar_credenciales, actualizar_token

from datetime import datetime, timezone, timedelta


def _token_ttl_minutes() -> int:
    raw = os.environ.get("AUTH_TOKEN_TTL_MINUTES", "60")
    try:
        value = int(raw)
    except ValueError:
        return 60
    return max(1, value)


def registrar_usuario_auth() -> tuple[Response, int] | Response:
    """Handler para POST /auth/registro.

    - Crea el usuario correctamente.
    - Guarda la contraseña mediante un hash en password_hash.
    """
    parsed, error = auth_common.parse_register_body()
    if error is not None:
        return error
    assert parsed is not None
    username = parsed["username"]
    nombre = parsed["nombre"]
    password = parsed["password"]

    dup_error = auth_common.ensure_username_unique(username)
    if dup_error is not None:
        return dup_error

    usuario = auth_common.crear_usuario_basico(nombre)
    usuario_id = usuario["id"]

    # 4. HASHEAR la contraseña
    password_hash = generate_password_hash(password)

    # 5. GUARDAR en la tabla 'credenciales'
    guardar_credenciales(usuario_id, username, password_hash)
    return jsonify({
        "id": usuario_id,
        "username": username,
        "nombre": nombre
    }), 201


def login() -> tuple[Response, int] | Response:
    """Handler para POST /auth/login.
    - Verifica la contraseña usando hashes.
    - Genera un token con fecha de expiración real.
    """
    parsed, error = auth_common.parse_login_body()
    if error is not None:
        return error

    username = parsed["username"]
    password = parsed["password"]

    # Busco el usuario en la base de datos
    cred, error = auth_common.get_credenciales_or_401(username)
    if error is not None:
        return error

    # Esto compara el hash con la contraseña escrita
    if not check_password_hash(cred["password_hash"], password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = uuid4().hex

    # Expiración
    ttl_minutes = _token_ttl_minutes()
    expira_en = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)

    # Guardamos el token y su fecha de expiración
    actualizar_token(cred["usuario_id"], token, expira_en.isoformat())

    return jsonify({"token": token}), 200


def obtener_usuario_actual() -> int | None:
    """Devuelve usuario_id asociado al token o None.

    - chequea expiración del token (token_expita_en).
    """
    token = auth_common.extraer_token_de_header()
    if not token:
        return None

    data = auth_common.obtener_datos_token(token)
    if data is None:
        return None

    expira_en = data.get("token_expira_en")
    if not expira_en:
        return None

    expira_en = datetime.fromisoformat(expira_en)

    if datetime.now(timezone.utc) > expira_en:
        return None

    usuario_id = data.get("usuario_id")
    return int(usuario_id) if usuario_id is not None else None

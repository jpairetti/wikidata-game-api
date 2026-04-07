"""
Tests que debés implementar: casos borde de la lista de juegos.
Contrato: POST con juego_id (id del catálogo). Completar según openapi.yaml.
"""

import json
from flask import request
import pytest
from src.store import CATALOGO_JUEGOS

@pytest.fixture
def usuario_id(client):
    r = client.post("/usuarios", json={"nombre": "UsuarioBorde"})
    assert r.status_code == 201
    return r.get_json()["id"]


def test_agregar_juego_falta_campo_obligatorio_400(client, usuario_id):
    """
    El contrato dice que requestBody:required.
    ref: '#/components/schemas/AgregarAListaInput'
        -required: [juego_id, tengo, quiero, jugado, me_gusta]
    si los campos requeridos no estan -> 404
    """
    request_body = {
        "tengo": True,
        "quiero": False,
        # omito varios campos
    }

    respuesta = client.post(f"/usuarios/{usuario_id}/juegos", json=request_body)

    assert respuesta.status_code == 400


def test_actualizar_juego_id_inexistente_404(client, usuario_id):
    # TODO: PUT /usuarios/<id>/juegos/Q99999 (no en lista) debe devolver 404
    respuesta = client.put(f"/usuarios/{usuario_id}/juegos/Q99999")
    assert respuesta.status_code == 404


def test_eliminar_juego_no_en_lista_404(client, usuario_id):
    # TODO: DELETE /usuarios/<id>/juegos/<juego_id> con juego no en la lista debe devolver 404
    respuesta = client.delete(f"/usuarios/{usuario_id}/juegos/Q99999")
    assert respuesta.status_code == 404


def test_agregar_juego_id_inexistente_404(client, usuario_id):
    request_body = {
        "juego_id": "Q999999999",
        "tengo": False,
        "quiero": False,
        "jugado": False,
        "me_gusta": False
    }
    
    respuesta = client.post(f"/usuarios/{usuario_id}/juegos", json=request_body)

    assert respuesta.status_code == 404


def test_ordenar_por_fecha_lanzamiento_REAL(client, usuario_id):
    request_b1 = {
        "juego_id": "Q67387683",
        "tengo": True,
        "quiero": False,
        "jugado": True,
        "me_gusta": True
    }

    request_b2 = {
        "juego_id": "Q105729297",
        "tengo": True,
        "quiero": False,
        "jugado": True,
        "me_gusta": True
    }
    client.post(f"/usuarios/{usuario_id}/juegos", json=request_b1)
    client.post(f"/usuarios/{usuario_id}/juegos", json=request_b2)

    respuesta = client.get(f"/usuarios/{usuario_id}/juegos?ordenar=fecha_lanzamiento")
    #chequeo respuesta para focalizar el test
    assert respuesta.status_code == 200
    #json format
    datos = respuesta.get_json() 
    
    assert datos[0]["lanzamiento"] <= datos[1]["lanzamiento"]
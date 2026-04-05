"""
Tests que debés implementar: sugerencia con filtro por género.
Completar los tests según el contrato de la API.
"""

import pytest


def test_sugerencia_con_genero_solo_devuelve_ese_genero(client):
    from src.store import CATALOGO_JUEGOS

    #  Creo usuario
    r_reg = client.post("/auth/registro", json={
        "username": "joaquin",
        "nombre": "pairetti",
        "password": "123456"
    })
    usuario_id = r_reg.get_json()["id"]

    CATALOGO_JUEGOS.clear()
    CATALOGO_JUEGOS["Q1"] = {
        "nombre": "Minecraft",
        "genero": "sandbox",
        "lanzamiento": "2011",
        "descripcion": "",
        "plataforma": ""
    }
    CATALOGO_JUEGOS["Q2"] = {
        "nombre": "Call of Duty",
        "genero": "shooter",
        "lanzamiento": "2003",
        "descripcion": "",
        "plataforma": ""
    }

    client.post(f"/usuarios/{usuario_id}/juegos", json={
        "juego_id": "Q1",
        "tengo": True,
        "quiero": False,
        "jugado": True,
        "me_gusta": True
    })

    client.post(f"/usuarios/{usuario_id}/juegos", json={
        "juego_id": "Q2",
        "tengo": True,
        "quiero": False,
        "jugado": True,
        "me_gusta": True
    })

    respuesta = client.get(f"/usuarios/{usuario_id}/sugerencia?genero=sandbox")

    assert respuesta.status_code == 200

    data = respuesta.get_json()


    assert data["genero"] == "sandbox"



def test_sugerencia_genero_sin_coincidencias_404(client):
    # TODO: Sin juegos del género pedido debe devolver 404

    nombre_user = "j"
    r_reg = client.post("/auth/registro", json={"username": nombre_user, "nombre": "p", "password": "123456"})

    datos_user = r_reg.get_json()
    usuario_id = datos_user["id"]
    
    ruta = f"/usuarios/{usuario_id}/sugerencia?genero={"videojuego de supervivencia"}"
    respuesta = client.get(ruta)
    
    assert respuesta.status_code == 404

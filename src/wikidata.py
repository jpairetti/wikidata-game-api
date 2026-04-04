"""Cliente Wikidata: búsqueda, obtención por id y población del catálogo local.

Qué es este módulo:
    Integración con la API de Wikidata para buscar y obtener videojuegos (Q7889).
    Los resultados se mapean a un formato común (id, nombre, genero, lanzamiento,
    plataforma, descripcion) y se guardan en store.CATALOGO_JUEGOS.

Para qué sirve:
    - Permitir búsqueda de juegos por texto (GET /juegos?q=...&fuente=wikidata).
    - Resolver un juego por Q-id si no está en catálogo (obtener_juego).
    - Poblar/ampliar el catálogo local con datos de Wikidata, usando
      `store.CATALOGO_JUEGOS` como estructura central (análogo a `store.USUARIOS`
      para los usuarios).

Qué hace:
    - buscar(q): busca en Wikidata, filtra videojuegos, mapea y guarda en catálogo; None si falla API.
    - obtener_juego(juego_id): devuelve juego desde catálogo o Wikidata; None si no existe o falla.
    - listar_o_buscar_juegos: GET /juegos (lista catálogo, búsqueda local o wikidata); 502 si falla Wikidata.
    - obtener_juego_endpoint: GET /juegos/<id>; 404 si no encontrado.

Qué se espera que hagas:
    En el kickstarter las funciones públicas pueden venir con stubs. Implementá
    buscar y obtener_juego usando las helpers _request, _mapear_entidad,
    _obtener_labels, etc., y devolved None cuando la API falle; el endpoint
    debe responder 502 cuando buscar devuelve None.
"""

import logging
import os
import requests
from flask import request, jsonify

from .store import CATALOGO_JUEGOS, _persist_catalogo
from . import filtros

logger = logging.getLogger(__name__)

WIKIDATA_BASE = "https://www.wikidata.org/w/api.php"
WIKIDATA_TIMEOUT = 10
VIDEO_GAME_QID = "Q7889"
LANG = "es"
P_DATE = "P577"
P_GENRE = "P136"
P_PLATFORM = "P400"
P_INSTANCE_OF = "P31"


def _get_user_agent() -> str:
    """Devuelve el User-Agent para las peticiones a Wikidata (env WIKIDATA_USER_AGENT o default)."""
    return os.environ.get("WIKIDATA_USER_AGENT", "LabRedes2026/1.0").strip() or "LabRedes2026/1.0"


def _request(params: dict) -> dict | None:
    """Hace GET a la API de Wikidata con los params dados. Añade format=json y User-Agent.

    Args:
        params: Parámetros de query para w/api.php (action, ids, etc.).

    Returns:
        Dict con la respuesta JSON; None si hay error de red, timeout o JSON inválido.
    """

    headers = {"User-Agent": _get_user_agent()}
    params["format"] = "json"
    
    try:
        resp = requests.get(WIKIDATA_BASE, params = params, headers = headers, timeout = WIKIDATA_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    
    except(requests.RequestException, ValueError):
        return None


def _extraer_fecha(time_value: str) -> str:
    """Convierte un valor time de Wikidata (ej. +2020-01-15T00:00:00Z) a string YYYY-MM-DD.

    Args:
        time_value: Valor time tal como viene en claims.

    Returns:
        String de fecha (hasta 10 caracteres) o cadena vacía.
    """
    if not time_value:
        return ""
    s = time_value.replace("T00:00:00Z", "").replace("T00:00:00Z", "").strip()
    if s.startswith("+"):
        s = s[1:]
    return s[:10] if len(s) >= 10 else s


def _obtener_labels(qids: list[str]) -> dict[str, str]:
    """Obtiene los labels (nombres) en español o inglés para una lista de Q-ids.

    Args:
        qids: Lista de Q-ids (máx. 50).

    Returns:
        Dict qid -> valor del label (string).
    """

    if not qids:
        return {}
    
    data = _request({
        "action": "wbgetentities",
        "ids": "|".join(qids),
        "props": "labels",
        "languages": LANG
    })

    if data is None:
        return None
    
    entities = data.get("entities", {})

    labels = {}
    for qid, ent in entities.items():
        labels = ent.get("labels", {})

        if LANG in labels:
            valor = labels[LANG]["value"]
        elif "en" in labels:
            valor = labels["en"]["value"]
        else:
            valor = ""

        labels[qid] = valor

    return labels
    if not qids:
        return {}
    
    data = _request({
        "action": "wbgetentities",
        "ids": "|".join(qids),
        "props": "labels",
        "languages": LANG  # Wikidata prefiere el plural aquí
    })

    if data is None:
        return {} # Mejor devolver vacío que None para no romper el resto

    entidades = data.get("entities", {})
    resultados = {}

    # Empezamos la limpieza
    for qid, info in entidades.items():
        # Por defecto, si no hay nombre, que al menos nos deje el QID
        nombre_final = qid 
        
        labels = info.get("labels", {})
        
        # 1. Intentamos en español
        if LANG in labels:
            nombre_final = labels[LANG].get("value", qid)
        # 2. Si no hay, intentamos en inglés
        elif "en" in labels:
            nombre_final = labels["en"].get("value", qid)
            
        resultados[qid] = nombre_final

    return resultados


def _claim_value_id(claims: dict, prop: str) -> str:
    """Extrae el id (Q-id) del primer claim de una propiedad.

    Args:
        claims: Dict de claims de la entidad.
        prop: Id de propiedad (ej. P136, P400).

    Returns:
        Q-id del valor o cadena vacía.
    """
    if prop not in claims or not claims[prop]:
        return ""
    c = claims[prop][0]
    return c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "") or ""


def _claim_value_time(claims: dict, prop: str) -> str:
    """Extrae el valor time del primer claim de una propiedad (ej. P577 fecha lanzamiento).

    Args:
        claims: Dict de claims de la entidad.
        prop: Id de propiedad.

    Returns:
        Valor time (string) o cadena vacía.
    """
    if prop not in claims or not claims[prop]:
        return ""
    c = claims[prop][0]
    return c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("time", "") or ""


def _mapear_entidad(ent: dict, labels_cache: dict[str, str]) -> dict:
    """Convierte una entidad Wikidata a dict juego (id, nombre, genero, lanzamiento, plataforma, descripcion).

    Args:
        ent: Entidad tal como viene de wbgetentities.
        labels_cache: Dict Q-id -> label para resolver género y plataforma.

    Returns:
        Dict con id, nombre, genero, lanzamiento, plataforma, descripcion.
    """
    labels = ent.get("labels", {})
    descriptions = ent.get("descriptions", {})
    claims = ent.get("claims", {})
    qid = ent.get("id", "")
    for lang in (LANG, "en"):
        if lang in labels:
            nombre = labels[lang].get("value", "")
            break
    else:
        nombre = ""
    desc = ""
    for lang in (LANG, "en"):
        if lang in descriptions:
            desc = descriptions[lang].get("value", "")
            break
    lanzamiento = _extraer_fecha(_claim_value_time(claims, P_DATE))
    genero_q = _claim_value_id(claims, P_GENRE)
    plataforma_q = _claim_value_id(claims, P_PLATFORM)
    genero = labels_cache.get(genero_q, "") if genero_q else ""
    plataforma = labels_cache.get(plataforma_q, "") if plataforma_q else ""
    return {
        "id": qid,
        "nombre": nombre,
        "genero": genero,
        "lanzamiento": lanzamiento,
        "plataforma": plataforma,
        "descripcion": desc,
    }


def _es_videojuego(ent: dict) -> bool:
    """Indica si la entidad tiene P31=Q7889 (instance of video game).

    Args:
        ent: Entidad Wikidata (con claims).

    Returns:
        True si es videojuego, False si no.
    """
    # usa wbgetentities, busca en el campo claims de la entidad

    claims = ent.get("claims", {})
    
    if P_INSTANCE_OF not in claims:
        return False
    
    # revisa que el id sea VIDEO_GAME_QID
    for clm in claims[P_INSTANCE_OF]:
        v = clm.get("mainsnak", {}).get("datavalue", {})
        value = v.get("value", {})

        if value["id"] == VIDEO_GAME_QID:
            return True

    return False


def _buscar_ids_wikidata(q: str) -> list[str] | None:
    """Busca entidades en Wikidata por texto y devuelve sus ids.

    Args:
        q: Texto de búsqueda.

    Returns:
        Lista de Q-ids encontrados; None si falla la API; [] si sin resultados.
    """
    # usa wbsearchentities
    data = _request({
        "action": "wbsearchentities",
        "search": q,
        "language": LANG,
    })

    if data is None:
        return None

    # guarda ids del campo search en una lista 
    ids = []
    for item in data.get("search", []):
        ids.append(item["id"])
    return ids



def _filtrar_ids_videojuegos(ids: list[str]) -> list[str] | None:
    """Filtra la lista de ids dejando solo los que son videojuegos (P31=Q7889).

    Args:
        ids: Lista de Q-ids a comprobar.

    Returns:
        Lista de ids que son videojuegos; None si falla la API; [] si ninguno.
    """
    if not ids:
        return []
    
    # pide las entidades de la lista de ids (concatenadas de la forma q1|q2|q3|...|qn)
    data = _request({
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": "claims",
    })

    if data is None:
        return None

    # guarda solo el campo entities 
    entities = data.get("entities", {})

    lista_videojuegos = []
    for qid, ent in entities.items():
        if _es_videojuego(ent):
            lista_videojuegos.append(qid)
    return lista_videojuegos



def _entidades_completas_videojuegos(video_game_ids: list[str]) -> dict | None:
    """Obtiene entidades completas (labels, descriptions, claims) para los ids dados.

    Args:
        video_game_ids: Lista de Q-ids de videojuegos.

    Returns:
        Dict qid -> entidad; None si falla la API; {} si la lista está vacía.
    """
    if not video_game_ids:
        return {}
    
    data = _request({
        "action": "wbgetentities",
        "ids": "|".join(video_game_ids),
        "props": "labels|descriptions|claims",
    })

    if data is None:
        return None
    
    return data.get("entities", {})


def _colectar_ref_qids(entities: dict) -> set:
    """Extrae los Q-ids de género (P136) y plataforma (P400) de las entidades.

    Args:
        entities: Dict qid -> entidad con claims.

    Returns:
        Set de Q-ids a resolver para labels (genero, plataforma).
    """
    ref_qids = set()
    for ent in entities.values():
        if "missing" in ent:
            continue
        claims = ent.get("claims", {})
        for q in (_claim_value_id(claims, P_GENRE), _claim_value_id(claims, P_PLATFORM)):
            if q:
                ref_qids.add(q)
    return ref_qids


def _mapear_y_guardar_resultados(
    video_game_ids: list[str], entities: dict, labels_cache: dict[str, str]
) -> list[dict]:
    """Mapea entidades a formato juego, las guarda en CATALOGO_JUEGOS y devuelve la lista.

    Args:
        video_game_ids: Orden de ids a incluir.
        entities: Dict qid -> entidad.
        labels_cache: Dict Q-id -> label para género/plataforma.

    Returns:
        Lista de dicts de juegos (id, nombre, genero, etc.); se omiten entidades missing.
    """
    resultados = []
    for qid in video_game_ids:
        ent = entities.get(qid, {})
        if "missing" in ent:
            continue
        ent = dict(ent)
        ent["id"] = qid
        juego = _mapear_entidad(ent, labels_cache)
        CATALOGO_JUEGOS[qid] = juego
        resultados.append(juego)
    _persist_catalogo()
    return resultados


def buscar(q: str) -> list[dict] | None:
    """Busca en Wikidata por texto, filtra videojuegos, mapea y guarda en catálogo.

    Args:
        q: Texto de búsqueda.

    Returns:
        Lista de juegos (dict con id, nombre, genero, etc.); None si falla la API;
        [] si no hay resultados o ninguno es videojuego.
    """
    ids = _buscar_ids_wikidata(q)
    if ids is None:
        return None
    
    vjuegos = _filtrar_ids_videojuegos(ids)
    if vjuegos is None:
        return []

    entities = _entidades_completas_videojuegos(vjuegos)
    if entities is None:
        return None


    ref = _colectar_ref_qids(entities)
    labels = _obtener_labels(list[str](ref))

    return _mapear_y_guardar_resultados(vjuegos, entities, labels)


def obtener_juego(juego_id: str) -> dict | None:
    """Obtiene un juego por Q-id: primero catálogo local, si no está consulta Wikidata y guarda.

    Args:
        juego_id: Q-id del juego (ej. Q12345).

    Returns:
        Dict del juego (id, nombre, genero, lanzamiento, plataforma, descripcion);
        None si no existe o falla la API.
    """
    if juego_id in CATALOGO_JUEGOS:
        return CATALOGO_JUEGOS[juego_id]
    
    entities = _entidades_completas_videojuegos([juego_id])

    if entities is None:
        return None
    
    ent = entities.get(juego_id)
    if not ent: 
        return None
    
    if not _es_videojuego(ent):
        return None
    
    ref = _colectar_ref_qids(entities)
    labels = _obtener_labels(list(ref))
    if labels is None:
        return None

    resultados = _mapear_y_guardar_resultados([juego_id], entities, labels)
    
    # En lugar de 'return resultados', hacemos esto:
    if resultados and len(resultados) > 0:
        return resultados[0]  # Retorna el DICCIONARIO del juego
        
    return None
    

def _obtener_lista_juegos_para_get() -> tuple[list[dict] | None, tuple | None]:
    """Resuelve la lista de juegos para GET /juegos según query params q y fuente.

    Sin q: devuelve todo el catálogo. Con q y fuente=local: filtra por nombre en catálogo.
    Con q y fuente=wikidata: llama a buscar(q); si falla devuelve error 502.

    Returns:
        (lista, None) con la lista de juegos a devolver; o (None, (response, 502)) si falla Wikidata.
    """
    q = request.args.get("q", "").strip()
    fuente = request.args.get("fuente", "local").strip().lower()
    if not q:
        return list(CATALOGO_JUEGOS.values()), None
    if fuente == "wikidata":
        resultados = buscar(q)
        if resultados is None:
            return None, (jsonify({"error": "Error al consultar Wikidata"}), 502)
        return list(resultados or []), None
    q_lower = q.lower()
    return [j for j in CATALOGO_JUEGOS.values() if q_lower in (j.get("nombre") or "").lower()], None



def listar_o_buscar_juegos():
    """Handler GET /juegos: listar catálogo o buscar por q con fuente local o wikidata.

    Query params: q (opcional), fuente (local|wikidata), genero, ordenar, orden.

    Returns:
        Response: JSON con lista de juegos y 200; 502 si fuente=wikidata y falla la API.
    """
    # devuelve la lista de juegos exxtraidas localmente o de wikidata 
    lista, error = _obtener_lista_juegos_para_get()
    
    if error:
        return error

    # filtro la lista por genero. Ordeno asc
    resultado_final = filtros.filtrar_y_ordenar(
        lista,
        genero=request.args.get("genero"),
        ordenar=request.args.get("ordenar"),
        orden = request.args.get("orden", "asc")
    )
    
    return jsonify(resultado_final), 200


def obtener_juego_endpoint(juego_id: str):
    """Handler GET /juegos/<id>: devuelve un juego por Q-id (catálogo o Wikidata).

    Args:
        juego_id: Q-id del juego.

    Returns:
        Response: JSON del juego y 200; 404 si no encontrado o falla la API.
    """
    
    juego = obtener_juego(juego_id)
    if juego is None:
        return jsonify({"error": "juego no encontrado"}), 404

    return jsonify(juego), 200
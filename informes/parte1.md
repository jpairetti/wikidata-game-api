## Ejercicio 1 — Busqueda "zelda"
### Comando:
```bash
curl -A "LabRedes2026/1.0" "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=zelda&language=es&format=json" \
  | python3 -m json.tool
```
---
#### - ¿Que valor aparece en la clave searchinfo.search? 
- searchinfo.search: "zelda"
---
#### - En la lista search, elegí un resultado que parezca un videojuego: ¿cuál es su id (Q-id), label y description?
Juego encontrado:
- "id": "Q12395"
- "label": "The Legend of Zelda",
- "description": "1986 action-adventure video game"
---

## Ejercicio 2 - Obtener una entidad por ID
### Comando:
```bash
curl -A "LabRedes2026/1.0" "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q12395&format=json&props=labels|descriptions" \
  | python3 -m json.tool
```
---
#### - Dentro de `entities.<QID>.labels`, ¿qué `value` aparece para el idioma `es` y para `en`?
- "en": {
            "language": "en",
            "value": "The Legend of Zelda"
        }
- "es": {
            "language": "es",
            "value": "The Legend of Zelda"
        }
---
#### - Dentro de `entities.<QID>.descriptions`, ¿qué descripción en `es` te devuelve para ese juego?
- "es": {
            "language": "es",
            "value": "videojuego de 1986"
        }
---

## Ejercicio 3 — Búsqueda con el término "mario" y límite
### Comando:
```bash
curl -A "LabRedes2026/1.0" "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=mario&language=es&limit=5&format=json" \
  | python3 -m json.tool
```
---
#### - ¿Cuántos elementos hay en la lista `search` cuando usás `limit=5`?
- Hay 5 elementos.
---
#### - ¿Encontrás en los resultados algún videojuego de la saga Mario? ¿Cuál es su `id` y su `description`?
- Con `limit=5` no aparecieron videojuegos en los resultados, ya que Wikidata devuelve entidades generales (personas, lugares) antes que videojuegos.
---

## Ejercicio Adicional — Paginación con el parámetro continue
### Consigna: Obtener resultados de búsqueda en páginas usando limit y continue, para no traer todos los resultados de una vez.
---
### Comandos:
**Comando para la pagina 1:**
```bash
curl -A "LabRedes2026/1.0" "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=zelda&language=es&limit=3&format=json" | python3 -m json.tool
```
- En la respuesta que hay un campo llamado search-continue con un numero. Ese numero es el que se utiliza en el siguiente comando.
---
**Comando para la pagina 2:**

**Parametro nuevo: - `continue=3` (desde qué resultado continuar)**
```bash
curl -A "LabRedes2026/1.0" "https://www.wikidata.org/w/api.php?action=wbsearchentities&search=zelda&language=es&limit=3&format=json&continue=3" | python3 -m json.tool
```
---
**Resultado relevante:**
Si observas los 3 resultados del comando 1 y los 3 del comando 2 son distintos, son paginas diferentes de la misma busqueda.

**Pagina 1 — resultados:**
- "id": "Q2438689"
- "id": "Q12395"
- "id": "Q2571225"

**Pagina 2 — resultados:**
- "id": "Q106595460"
- "id": "Q12393"
- "id": "Q18420744"
---
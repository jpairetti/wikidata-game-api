
#### listar usuarios
```
[]
```

#### crear usuarios (4 veces)

```
{
    "id": 1,
    "nombre": "Messi"
}
{
    "id": 2,
    "nombre": "Ronaldo"
}
{
    "id": 3,
    "nombre": "Neymar"
}
{
    "id": 4,
    "nombre": "Mat\u00edas"
}
```
#### listar usuarios

```
[
    {
        "id": 1,
        "nombre": "Messi"
    },
    {
        "id": 2,
        "nombre": "Ronaldo"
    },
    {
        "id": 3,
        "nombre": "Neymar"
    },
    {
        "id": 4,
        "nombre": "Matias"
    }
]
```
#### obtener usuario 2
```
{
    "id": 2,
    "nombre": "Ronaldo"
}
```
#### actualizar usuario 4
```
{
    "id": 4,
    "nombre": "Mbappe"
}
```
#### listar usuarios
```
[
    {
        "id": 1,
        "nombre": "Messi"
    },
    {
        "id": 2,
        "nombre": "Ronaldo"
    },
    {
        "id": 3,
        "nombre": "Neymar"
    },
    {
        "id": 4,
        "nombre": "Mbappe"
    }
]
```
#### delete usuario 1
```
{
    "mensaje": "usuario eliminado"
}
```

#### obtener usuario 1
```
{
    "error": "user not found"
}
```
#### listar usuarios

```
[
    {
        "id": 2,
        "nombre": "Ronaldo"
    },
    {
        "id": 3,
        "nombre": "Neymar"
    },
    {
        "id": 4,
        "nombre": "Neymar"
    }
]
```
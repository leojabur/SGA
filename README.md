# Python Panel App (inspired by `novosga/panel-app`)

Este repositório contém uma implementação em Python de um painel de chamadas.

## Funcionalidades

- API HTTP para registrar chamadas (`POST /api/calls`)
- API HTTP para listar estado atual (`GET /api/state`)
- Front-end simples em HTML para exibir a última chamada e histórico
- Persistência em memória com histórico limitado

## Executar

```bash
python panel_app.py
```

Acesse: <http://127.0.0.1:8000>

## Exemplo de chamada

```bash
curl -X POST http://127.0.0.1:8000/api/calls \
  -H 'Content-Type: application/json' \
  -d '{"ticket":"A-123","desk":"Guichê 2","service":"Cadastro"}'
```


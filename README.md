# Python Panel App (inspired by `novosga/panel-app`)

Este repositório contém uma implementação em Python de um painel de chamadas.

## Funcionalidades

- API HTTP para registrar chamadas (`POST /api/calls`)
- API HTTP para listar estado atual (`GET /api/state`)
- API de configuração do servidor NovoSGA (`GET/POST /api/config`)
- Front-end com formulário para configuração de conexão
- Persistência em memória para chamadas e em arquivo JSON para configuração

## Configurações de conexão (NovoSGA)

Campos implementados:

- **Servidor**: URL do NovoSGA (ex: `http://127.0.0.1`)
- **Usuário**: nome de usuário com acesso ao NovoSGA
- **Senha**: senha do usuário
- **Client ID**: ID do cliente da Web API
- **Client Secret**: senha do cliente da Web API
- **Unidade**: unidade de atendimento do painel
- **Serviços**: serviços que serão chamados no painel
- **Alerta**: som para tocar quando nova senha for chamada

A configuração é salva em `panel_config.json` (ajustável com `PANEL_CONFIG_FILE`).

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

## Exemplo de configuração

```bash
curl -X POST http://127.0.0.1:8000/api/config \
  -H 'Content-Type: application/json' \
  -d '{
    "server_url":"http://127.0.0.1",
    "username":"admin",
    "password":"secret",
    "client_id":"client-id",
    "client_secret":"client-secret",
    "unit":"Unidade Central",
    "services":["Triagem", "Cadastro"],
    "alert_sound":"beep.mp3"
  }'
```

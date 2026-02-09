from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple

from panel.config import ConfigStore
from panel.core import PanelState

state = PanelState(max_history=20)
config_store = ConfigStore(path=os.getenv("PANEL_CONFIG_FILE", "panel_config.json"))


def _parse_call_payload(body: bytes) -> Tuple[bool, dict | str]:
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return False, "JSON inválido"

    ticket = str(payload.get("ticket", "")).strip()
    desk = str(payload.get("desk", "")).strip()
    service = str(payload.get("service", "")).strip()

    if not ticket or not desk:
        return False, "Campos obrigatórios: ticket e desk"

    return True, {"ticket": ticket, "desk": desk, "service": service}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            self._json(HTTPStatus.OK, state.snapshot())
            return

        if self.path == "/api/config":
            self._json(HTTPStatus.OK, {"config": config_store.public()})
            return

        if self.path == "/":
            self._html(INDEX_HTML)
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/calls":
            length = int(self.headers.get("Content-Length", "0"))
            ok, result = _parse_call_payload(self.rfile.read(length))
            if not ok:
                self._json(HTTPStatus.BAD_REQUEST, {"error": result})
                return

            payload = result
            call = state.register_call(
                ticket=payload["ticket"],
                desk=payload["desk"],
                service=payload["service"],
            )
            self._json(HTTPStatus.CREATED, {"call": call.__dict__})
            return

        if self.path == "/api/config":
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "JSON inválido"})
                return
            self._json(HTTPStatus.OK, {"config": config_store.update(payload)})
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})

    def log_message(self, fmt: str, *args) -> None:
        return


INDEX_HTML = """<!doctype html>
<html lang='pt-BR'>
<head>
  <meta charset='utf-8'/>
  <meta name='viewport' content='width=device-width, initial-scale=1'/>
  <title>Painel de Chamadas</title>
  <style>
    body { font-family: Arial, sans-serif; background: #10131a; color: #fff; margin: 0; }
    header { padding: 16px 24px; background: #1a2030; font-size: 1.3rem; font-weight: bold; }
    .wrap { padding: 20px; display: grid; gap: 16px; grid-template-columns: 1.5fr 1fr; }
    .card { background: #1a2030; border-radius: 12px; padding: 16px; }
    .big { font-size: 3rem; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; }
    td, th { padding: 8px; border-bottom: 1px solid #2b3346; text-align: left; }
    .config { grid-column: 1 / -1; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 10px; }
    input { width: 100%; box-sizing: border-box; padding: 8px; border-radius: 6px; border: 1px solid #334; background: #0e1220; color: #fff; }
    button { margin-top: 10px; padding: 10px 14px; border: 0; border-radius: 8px; background: #2a6fff; color: white; cursor: pointer; }
    #status { margin-top: 8px; color: #a7c4ff; }
  </style>
</head>
<body>
  <header>Painel de Chamadas (Python)</header>
  <div class='wrap'>
    <section class='card'>
      <div>Última chamada</div>
      <div id='ticket' class='big'>---</div>
      <div id='meta'>Aguardando chamada...</div>
    </section>
    <section class='card'>
      <div>Histórico recente</div>
      <table>
        <thead><tr><th>Senha</th><th>Guichê</th><th>Serviço</th></tr></thead>
        <tbody id='history'></tbody>
      </table>
    </section>

    <section class='card config'>
      <h3>Configuração NovoSGA</h3>
      <div class='grid'>
        <label>Servidor <input id='server_url' placeholder='http://127.0.0.1' /></label>
        <label>Usuário <input id='username' /></label>
        <label>Senha <input id='password' type='password' /></label>
        <label>Client ID <input id='client_id' /></label>
        <label>Client Secret <input id='client_secret' type='password' /></label>
        <label>Unidade <input id='unit' /></label>
        <label>Serviços <input id='services' placeholder='1,2,3 ou Nome A, Nome B' /></label>
        <label>Alerta <input id='alert_sound' placeholder='URL/base64 para som de alerta' /></label>
      </div>
      <button onclick='saveConfig()'>Salvar configuração</button>
      <div id='status'></div>
    </section>
  </div>
  <script>
    async function refresh() {
      const res = await fetch('/api/state');
      const data = await res.json();

      const last = data.last_call;
      document.getElementById('ticket').textContent = last ? last.ticket : '---';
      document.getElementById('meta').textContent = last
        ? `${last.desk}${last.service ? ' • ' + last.service : ''}`
        : 'Aguardando chamada...';

      const tbody = document.getElementById('history');
      tbody.innerHTML = '';
      for (const item of data.history) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${item.ticket}</td><td>${item.desk}</td><td>${item.service || '-'}</td>`;
        tbody.appendChild(tr);
      }
    }

    async function loadConfig() {
      const res = await fetch('/api/config');
      const data = await res.json();
      const cfg = data.config;
      for (const key of ['server_url','username','password','client_id','client_secret','unit','alert_sound']) {
        const el = document.getElementById(key);
        if (el) el.value = cfg[key] || '';
      }
      document.getElementById('services').value = (cfg.services || []).join(', ');
    }

    async function saveConfig() {
      const payload = {
        server_url: document.getElementById('server_url').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        client_id: document.getElementById('client_id').value,
        client_secret: document.getElementById('client_secret').value,
        unit: document.getElementById('unit').value,
        services: document.getElementById('services').value,
        alert_sound: document.getElementById('alert_sound').value,
      };

      const res = await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      document.getElementById('status').textContent = res.ok
        ? 'Configuração salva com sucesso.'
        : (data.error || 'Erro ao salvar');

      if (res.ok) {
        await loadConfig();
      }
    }

    setInterval(refresh, 1500);
    refresh();
    loadConfig();
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    host = os.getenv("PANEL_HOST", "0.0.0.0")
    port = int(os.getenv("PANEL_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Servidor em http://{host}:{port}")
    server.serve_forever()

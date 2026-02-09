from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Tuple
import os

from panel.core import PanelState

state = PanelState(max_history=20)


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

        if self.path == "/":
            self._html(INDEX_HTML)
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/calls":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada"})
            return

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
    .wrap { padding: 20px; display: grid; gap: 16px; grid-template-columns: 2fr 1fr; }
    .card { background: #1a2030; border-radius: 12px; padding: 16px; }
    .big { font-size: 3rem; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; }
    td, th { padding: 8px; border-bottom: 1px solid #2b3346; text-align: left; }
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

    setInterval(refresh, 1500);
    refresh();
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

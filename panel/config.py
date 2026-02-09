from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass
class ConnectionConfig:
    server_url: str = ""
    username: str = ""
    password: str = ""
    client_id: str = ""
    client_secret: str = ""
    unit: str = ""
    services: list[str] | None = None
    alert_sound: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["password"] = "***" if self.password else ""
        data["client_secret"] = "***" if self.client_secret else ""
        data["services"] = self.services or []
        return data


class ConfigStore:
    def __init__(self, path: str = "panel_config.json") -> None:
        self._path = Path(path)
        self._lock = Lock()
        self._config = ConnectionConfig(services=[])
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8") or "{}")
        self._config = self._from_payload(data, keep_existing_secrets=False)

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(asdict(self._config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _from_payload(
        self, payload: dict[str, Any], keep_existing_secrets: bool = True
    ) -> ConnectionConfig:
        base = self._config if keep_existing_secrets else ConnectionConfig(services=[])

        services_raw = payload.get("services", base.services or [])
        if isinstance(services_raw, str):
            services = [item.strip() for item in services_raw.split(",") if item.strip()]
        elif isinstance(services_raw, list):
            services = [str(item).strip() for item in services_raw if str(item).strip()]
        else:
            services = base.services or []

        password = str(payload.get("password", "")).strip()
        if password == "***":
            password = base.password

        client_secret = str(payload.get("client_secret", "")).strip()
        if client_secret == "***":
            client_secret = base.client_secret

        return ConnectionConfig(
            server_url=str(payload.get("server_url", base.server_url)).strip(),
            username=str(payload.get("username", base.username)).strip(),
            password=password,
            client_id=str(payload.get("client_id", base.client_id)).strip(),
            client_secret=client_secret,
            unit=str(payload.get("unit", base.unit)).strip(),
            services=services,
            alert_sound=str(payload.get("alert_sound", base.alert_sound)).strip(),
        )

    def update(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._config = self._from_payload(payload)
            self._save()
            return self._config.to_public_dict()

    def public(self) -> dict[str, Any]:
        with self._lock:
            return self._config.to_public_dict()

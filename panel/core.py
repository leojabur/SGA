from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import List, Optional


@dataclass(frozen=True)
class Call:
    ticket: str
    desk: str
    service: str
    called_at: str


class PanelState:
    """Estado central do painel com suporte a concorrência."""

    def __init__(self, max_history: int = 15) -> None:
        self._max_history = max_history
        self._history: List[Call] = []
        self._last_call: Optional[Call] = None
        self._lock = Lock()

    def register_call(self, ticket: str, desk: str, service: str = "") -> Call:
        call = Call(
            ticket=ticket.strip(),
            desk=desk.strip(),
            service=service.strip(),
            called_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._last_call = call
            self._history.insert(0, call)
            self._history = self._history[: self._max_history]
        return call

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "last_call": asdict(self._last_call) if self._last_call else None,
                "history": [asdict(item) for item in self._history],
            }

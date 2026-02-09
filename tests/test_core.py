from panel.core import PanelState


def test_register_call_updates_last_call_and_history() -> None:
    state = PanelState(max_history=2)

    first = state.register_call(ticket="A-001", desk="G1", service="Triagem")
    second = state.register_call(ticket="A-002", desk="G2", service="Cadastro")
    state.register_call(ticket="A-003", desk="G3", service="")

    snap = state.snapshot()
    assert snap["last_call"]["ticket"] == "A-003"
    assert len(snap["history"]) == 2
    assert snap["history"][0]["ticket"] == "A-003"
    assert snap["history"][1]["ticket"] == "A-002"
    assert first.ticket == "A-001"
    assert second.ticket == "A-002"

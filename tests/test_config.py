from panel.config import ConfigStore


def test_config_store_update_and_mask_secrets(tmp_path) -> None:
    path = tmp_path / "panel_config.json"
    store = ConfigStore(path=str(path))

    cfg = store.update(
        {
            "server_url": "http://127.0.0.1",
            "username": "admin",
            "password": "123456",
            "client_id": "cid",
            "client_secret": "sec",
            "unit": "Central",
            "services": "Triagem, Cadastro",
            "alert_sound": "beep.mp3",
        }
    )

    assert cfg["password"] == "***"
    assert cfg["client_secret"] == "***"
    assert cfg["services"] == ["Triagem", "Cadastro"]

    cfg2 = store.update({"password": "***", "client_secret": "***"})
    assert cfg2["password"] == "***"
    assert cfg2["client_secret"] == "***"

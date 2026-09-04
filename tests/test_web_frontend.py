import yaml
from fastapi.testclient import TestClient

from web.app import create_web_app


def test_root_page_uses_cortex_control_center_identity():
    with open("config.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    app = create_web_app(config).get_app()
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "CÓRTEX" in body or "CORTEX" in body
    assert "COMMAND" in body or "Command" in body or "CORE" in body

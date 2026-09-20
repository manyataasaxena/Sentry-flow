"""OpenAPI contract snapshot tests."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_openapi_schema_is_valid():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "SentryFlow"
    assert "paths" in schema
    assert "components" in schema


def test_openapi_snapshot_matches():
    snapshot_path = Path(__file__).parent / "snapshots" / "openapi.json"
    client = TestClient(app)
    current = client.get("/openapi.json").json()
    if snapshot_path.exists():
        expected = json.loads(snapshot_path.read_text())
        assert current == expected
    else:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(current, indent=2))
        assert True
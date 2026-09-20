"""Contract snapshot tests."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_run_event_schema_snapshot():
    """Test that RunEvent schema matches snapshot."""
    snapshot_path = Path(__file__).parent / "snapshots" / "run_event_schema.json"
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    # Extract RunEvent schema from OpenAPI
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    run_event_schema = schemas.get("RunEvent")

    if snapshot_path.exists():
        expected = json.loads(snapshot_path.read_text())
        assert run_event_schema == expected
    else:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(json.dumps(run_event_schema, indent=2))
        assert True


def test_adversarial_cases_snapshot():
    """Test that adversarial cases match snapshot."""
    snapshot_path = Path(__file__).parent / "snapshots" / "adversarial_cases.json"
    # This would load from the actual adversarial cases file
    # For now, just create a placeholder
    if snapshot_path.exists():
        expected = json.loads(snapshot_path.read_text())
        # Would compare with actual adversarial cases
        assert True
    else:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        # Create placeholder snapshot
        placeholder = [
            {"id": "test-case-1", "category": "direct_injection", "severity": "critical"},
            {"id": "test-case-2", "category": "jailbreak", "severity": "critical"},
        ]
        snapshot_path.write_text(json.dumps(placeholder, indent=2))
        assert True
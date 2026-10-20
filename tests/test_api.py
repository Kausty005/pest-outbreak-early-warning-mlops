from __future__ import annotations

import json

import joblib
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def _client_with_artifact(tmp_path, fitted_model):
    joblib.dump(fitted_model, tmp_path / "crop_model.joblib")
    (tmp_path / "metadata.json").write_text(
        json.dumps(
            {
                "model_version": "test-model-1",
                "dataset": {"checksum_sha256": "test-checksum", "numeric_ranges": {}},
                "selected_model": {"model": "random_forest"},
                "evaluation_metrics": {"accuracy": 1.0, "macro_f1": 1.0, "weighted_f1": 1.0},
            }
        )
    )
    return TestClient(create_app(Settings(artifact_dir=tmp_path)))


def test_prediction_response_schema_and_invalid_requests(tmp_path, fitted_model):
    with _client_with_artifact(tmp_path, fitted_model) as client:
        payload = {"N": 1, "P": 6, "K": 6, "temperature": 18, "humidity": 40, "ph": 5.1, "rainfall": 31}
        response = client.post("/api/v1/crop/recommend", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["model_version"] == "test-model-1"
        assert len(body["top_recommendations"]) == 3
        assert body["persistence_status"] == "disabled"
        invalid = client.post("/api/v1/crop/recommend", json={**payload, "humidity": "nan"})
        assert invalid.status_code == 422


def test_model_loading_failure_is_visible_without_stacktrace(tmp_path):
    with TestClient(create_app(Settings(artifact_dir=tmp_path))) as client:
        assert client.get("/health").json()["model_available"] is False
        response = client.post("/api/v1/crop/recommend", json={"N": 1, "P": 1, "K": 1, "temperature": 20, "humidity": 50, "ph": 6, "rainfall": 20})
        assert response.status_code == 503
        assert "Traceback" not in response.text

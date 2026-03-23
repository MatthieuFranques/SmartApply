import json
import pytest
from unittest.mock import patch, mock_open


class TestFilterStart:

    def test_start_filter_success(self, client):
        """Pipeline de filtrage → 200 + summary."""
        mock_result = {
            "pre_kept":  [{"nom": "TestCorp"}],
            "deep_kept": [{"nom": "TestCorp"}],
            "paths":     {"pre": "./results/pre.json", "deep": "./results/deep.json"},
        }
        with patch("app.routers.filter.run_pipeline", return_value=mock_result):
            response = client.post("/filter/start", json={"cities": ["Toulouse"]})
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["pre_kept"]  == 1
        assert data["summary"]["deep_kept"] == 1

    def test_start_filter_nothing_kept(self, client):
        """Aucune entreprise retenue → 422."""
        mock_result = {"pre_kept": [], "deep_kept": [], "paths": {}}
        with patch("app.routers.filter.run_pipeline", return_value=mock_result):
            response = client.post("/filter/start", json={"cities": ["Toulouse"]})
        assert response.status_code == 422

    def test_start_filter_missing_body(self, client):
        """Body invalide → 422."""
        response = client.post("/filter/start", json={})
        assert response.status_code == 422

    def test_start_filter_optional_params(self, client):
        """Paramètres optionnels acceptés."""
        mock_result = {
            "pre_kept":  [{"nom": "A"}, {"nom": "B"}],
            "deep_kept": [{"nom": "A"}],
            "paths":     {},
        }
        with patch("app.routers.filter.run_pipeline", return_value=mock_result):
            response = client.post("/filter/start", json={
                "cities":         ["Toulouse"],
                "min_prescore":   0.5,
                "min_deep_score": 0.7,
                "concurrency":    4,
                "skip_deep":      False,
            })
        assert response.status_code == 200


class TestFilterResults:

    def test_get_results_success(self, client, mock_company):
        """Retourne deep_results.json."""
        mock_data = json.dumps([mock_company])
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):
            response = client.get("/filter/results")
        assert response.status_code == 200
        assert response.json()[0]["nom"] == "TestCorp"

    def test_get_results_not_found(self, client):
        """Fichier absent → 404."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/filter/results")
        assert response.status_code == 404
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open


class TestEnrichStart:

    def test_start_enrich_success(self, client):
        """Enrichissement OK → 200 + summary."""
        mock_summary = MagicMock()
        mock_summary.__dict__ = {"total": 10, "enriched": 8, "errors": 2}

        with patch("app.routers.enrich.find_deep_results", return_value="./results/deep.json"), \
             patch("os.path.exists", return_value=True), \
             patch("app.routers.enrich.build_output_file", return_value="./results/enriched.json"), \
             patch("app.routers.enrich.run_enrich", return_value=mock_summary):
            response = client.post("/enrich/start", json={})
        assert response.status_code == 200
        assert "message" in response.json()

    def test_start_enrich_no_deep_results(self, client):
        """Pas de deep_results → 404."""
        with patch("app.routers.enrich.find_deep_results",
                   side_effect=FileNotFoundError("Aucun deep_results trouvé")):
            response = client.post("/enrich/start", json={})
        assert response.status_code == 404

    def test_start_enrich_input_file_not_found(self, client):
        """input_file fourni mais inexistant → 404."""
        with patch("app.routers.enrich.find_deep_results", return_value="./results/deep.json"), \
             patch("os.path.exists", return_value=False):
            response = client.post("/enrich/start", json={"input_file": "./results/deep.json"})
        assert response.status_code == 404

    def test_start_enrich_with_limit(self, client):
        """Paramètre limit accepté."""
        mock_summary = MagicMock()
        with patch("app.routers.enrich.find_deep_results", return_value="./results/deep.json"), \
             patch("os.path.exists", return_value=True), \
             patch("app.routers.enrich.build_output_file", return_value="./results/enriched.json"), \
             patch("app.routers.enrich.run_enrich", return_value=mock_summary):
            response = client.post("/enrich/start", json={"limit": 5})
        assert response.status_code == 200


class TestEnrichResults:

    def test_get_results_success(self, client, mock_company):
        """Retourne enriched.json."""
        mock_data = json.dumps([mock_company])
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):
            response = client.get("/enrich/results")
        assert response.status_code == 200
        assert response.json()[0]["nom"] == "TestCorp"

    def test_get_results_not_found(self, client):
        """Fichier absent → 404."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/enrich/results")
        assert response.status_code == 404

    def test_get_results_custom_dir(self, client, mock_company):
        """output_dir personnalisé."""
        mock_data = json.dumps([mock_company])
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):
            response = client.get("/enrich/results?output_dir=./custom")
        assert response.status_code == 200
import json
import pytest
from unittest.mock import patch, mock_open


class TestScrapingStart:

    def test_start_scraping_success(self, client):
        """Lance un scraping en arrière-plan → 200 + message."""
        with patch("app.routers.scraping.run_scraping") as mock_run:
            response = client.post("/scraping/start", json={
                "cities":     ["Toulouse"],
                "output_dir": "./results"
            })
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["cities"] == ["Toulouse"]

    def test_start_scraping_multiple_cities(self, client):
        """Plusieurs villes acceptées."""
        with patch("app.routers.scraping.run_scraping"):
            response = client.post("/scraping/start", json={
                "cities":     ["Toulouse", "Paris", "Lyon"],
                "output_dir": "./results"
            })
        assert response.status_code == 200
        assert len(response.json()["cities"]) == 3

    def test_start_scraping_missing_cities(self, client):
        """Body invalide → 422."""
        response = client.post("/scraping/start", json={})
        assert response.status_code == 422


class TestScrapingResults:

    def test_get_results_success(self, client, mock_company):
        """Retourne la liste des entreprises scrapées."""
        mock_data = json.dumps([mock_company])
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):
            response = client.get("/scraping/results")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["nom"] == "TestCorp"

    def test_get_results_file_not_found(self, client):
        """Fichier absent → 404."""
        with patch("os.path.exists", return_value=False):
            response = client.get("/scraping/results")
        assert response.status_code == 404

    def test_get_results_custom_output_dir(self, client, mock_company):
        """Paramètre output_dir personnalisé."""
        mock_data = json.dumps([mock_company])
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data)):
            response = client.get("/scraping/results?output_dir=./custom")
        assert response.status_code == 200
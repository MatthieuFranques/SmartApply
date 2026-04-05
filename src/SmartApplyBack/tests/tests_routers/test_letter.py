# import json
# import pytest
# from unittest.mock import patch, MagicMock, mock_open


# class TestLetterGenerate:

#     def test_generate_letter_success(self, client, mock_company):
#         """Génère une lettre → 201 + filename."""
#         mock_response = {
#             "company":    "TestCorp",
#             "filename":   "TestCorp.json",
#             "mode":       "letter_spontaneous",
#             "model":      "mistral",
#             "output_dir": "./letters",
#         }
#         with patch("app.routers.letter.check_ollama", return_value=True), \
#              patch("app.routers.letter.find_company", return_value=mock_company), \
#              patch("app.routers.letter.determine_mode", return_value="letter"), \
#              patch("app.routers.letter.generate_letter", return_value="Madame, Monsieur..."), \
#              patch("builtins.open", mock_open()), \
#              patch("json.dump"):
#             response = client.post("/letter/", json={"name": "TestCorp"})
#         assert response.status_code == 201
#         assert response.json()["company"] == "TestCorp"

#     def test_generate_ollama_unavailable(self, client):
#         """Ollama inaccessible → 503."""
#         with patch("app.routers.letter.check_ollama", return_value=False):
#             response = client.post("/letter/", json={"name": "TestCorp"})
#         assert response.status_code == 503

#     def test_generate_company_not_found(self, client):
#         """Entreprise inconnue → 404."""
#         with patch("app.routers.letter.check_ollama", return_value=True), \
#              patch("app.routers.letter.find_company",
#                    side_effect=Exception("404")):
#             response = client.post("/letter/", json={"name": "Inconnue"})
#         assert response.status_code in (404, 500)

#     def test_generate_missing_name(self, client):
#         """Body sans name → 422."""
#         response = client.post("/letter/", json={})
#         assert response.status_code == 422

#     def test_generate_contact_mode(self, client, mock_company):
#         """Mode contact_form déclenché correctement."""
#         with patch("app.routers.letter.check_ollama", return_value=True), \
#              patch("app.routers.letter.find_company", return_value=mock_company), \
#              patch("app.routers.letter.determine_mode", return_value="contact"), \
#              patch("app.routers.letter.generate_contact_form", return_value="Formulaire..."), \
#              patch("builtins.open", mock_open()), \
#              patch("json.dump"):
#             response = client.post("/letter/", json={"name": "TestCorp"})
#         assert response.status_code == 201
#         assert response.json()["mode"] == "contact"


# class TestLetterDetails:

#     def test_get_letter_success(self, client):
#         """Retourne le JSON de la lettre générée."""
#         mock_data = json.dumps({
#             "company": "TestCorp",
#             "mode":    "letter_spontaneous",
#             "content": "Madame, Monsieur...",
#         })
#         with patch("app.routers.letter.find_generated_file") as mock_find, \
#              patch("builtins.open", mock_open(read_data=mock_data)):
#             mock_find.return_value = MagicMock(suffix=".json", **{"__str__": lambda s: "TestCorp.json"})
#             response = client.get("/letter/details", params={"name": "TestCorp"})
#         assert response.status_code == 200

#     def test_get_letter_not_found(self, client):
#         """Lettre non générée → 404."""
#         with patch("app.routers.letter.find_generated_file",
#                    side_effect=Exception("404")):
#             response = client.get("/letter/details", params={"name": "Inconnue"})
#         assert response.status_code in (404, 500)
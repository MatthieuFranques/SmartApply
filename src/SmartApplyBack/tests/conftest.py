# tests/conftest.py
import os
import pytest

os.environ.setdefault("SECRET_KEY", "ci_test_secret_key_very_long_and_secure_32_chars")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("GOOGLE_CLIENT_ID", "fake-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "fake-secret")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test_db")
os.environ.setdefault("ENV", "development")

@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    """
    Cette fixture s'exécute avant chaque test.
    Elle force les variables si jamais un module les a déjà chargées comme None.
    """
    monkeypatch.setenv("SECRET_KEY", "ci_test_secret_key_very_long_and_secure_32_chars")

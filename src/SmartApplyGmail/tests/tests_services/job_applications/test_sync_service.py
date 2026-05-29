"""Integration-ish unit test for sync_candidatures (Gmail API + repo mocked)."""

import base64
from unittest.mock import MagicMock, patch

from app.services.job_applications import job_applications as ja
from app.services.job_applications import gmail_ollama_parser as parser


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


def _raw(msg_id, sender, subject, body):
    return {
        "id": msg_id,
        "threadId": f"thread_{msg_id}",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "Date", "value": "Mon, 12 May 2025 10:00:00 +0000"},
            ],
            "body": {"data": _b64(body)},
        },
    }


def test_sync_counts_new_and_ignored():
    service = MagicMock()
    users = service.users.return_value
    users.labels().list().execute.return_value = {"labels": [{"id": "L1", "name": "Candidatures"}]}
    users.messages().list().execute.return_value = {"messages": [{"id": "m1"}, {"id": "m2"}]}

    raws = {
        "m1": _raw("m1", '"Acme" <hr@acme.io>', "Entretien développeur",
                   "Nous souhaitons vous rencontrer en entretien."),
        "m2": _raw("m2", "jobalerts@linkedin.com", "Des offres qui vous correspondent", "spam"),
    }

    def get_msg(userId, id, format):
        m = MagicMock()
        m.execute.return_value = raws[id]
        return m

    users.messages().get.side_effect = get_msg

    repo = MagicMock()
    repo.find_by_user.return_value = []
    repo.get_last_sync.return_value = None
    repo.set_last_sync.return_value = "2025-05-12T10:00:00"

    parser.clear_cache()
    with patch.object(ja, "build", return_value=service), \
         patch.object(parser, "_ask_json", side_effect=RuntimeError("offline")):
        result = ja.sync_candidatures(access_token="tok", user_id="u1", repo=repo)

    assert result.total_analyses == 2
    assert result.nouvelles == 1      # Acme saved
    assert result.ignorees == 1       # linkedin alert ignored
    repo.save.assert_called_once()
    repo.set_last_sync.assert_called_once_with("u1")


def test_sync_missing_label_raises():
    service = MagicMock()
    service.users().labels().list().execute.return_value = {"labels": []}
    repo = MagicMock()
    repo.find_by_user.return_value = []
    repo.get_last_sync.return_value = None

    with patch.object(ja, "build", return_value=service):
        try:
            ja.sync_candidatures("tok", "u1", repo)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "introuvable" in str(e)

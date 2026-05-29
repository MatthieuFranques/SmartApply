"""Tests for JobRepository (Mongo collection mocked)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from bson import ObjectId

from app.repositories import job_repository as jr


def _db_with(col):
    db = MagicMock()
    db.__getitem__.return_value = col
    return db


def _doc(**over):
    base = {"_id": ObjectId(), "user_id": "u1", "domaine": "acme.io", "stage": "scraping"}
    base.update(over)
    return base


def test_save_many_upserts_each():
    col = MagicMock()
    jobs = [{"domaine": "a.io"}, {"domaine": "b.io"}]
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        n = jr.JobRepository().save_many(jobs, "u1", "scraping")
    assert n == 2
    assert col.update_one.call_count == 2
    assert col.update_one.call_args_list[0].kwargs.get("upsert") is True


def test_update_stage_returns_job():
    col = MagicMock()
    col.find_one_and_update.return_value = _doc(stage="deep")
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        job = jr.JobRepository().update_stage("u1", "acme.io", "deep", extra_fields={"prescore": 7})
    assert job is not None
    assert job.stage == "deep"
    assert isinstance(job.id, str)


def test_update_stage_missing_returns_none():
    col = MagicMock()
    col.find_one_and_update.return_value = None
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        assert jr.JobRepository().update_stage("u1", "ghost.io", "deep") is None


def test_find_by_stage_maps_jobs():
    col = MagicMock()
    col.find.return_value = [_doc(domaine="a.io"), _doc(domaine="b.io")]
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        jobs = jr.JobRepository().find_by_stage("u1", "scraping")
    assert {j.domaine for j in jobs} == {"a.io", "b.io"}


def test_find_by_user_filters_active():
    col = MagicMock()
    col.find.return_value = [_doc()]
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        jobs = jr.JobRepository().find_by_user("u1")
    assert len(jobs) == 1
    args = col.find.call_args[0][0]
    assert args["status"] == "active"


def test_find_eliminated():
    col = MagicMock()
    col.find.return_value = [_doc(status="eliminated")]
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        jobs = jr.JobRepository().find_eliminated("u1", "deep")
    assert len(jobs) == 1
    assert col.find.call_args[0][0]["status"] == "eliminated"


def test_find_one_hit_and_miss():
    col = MagicMock()
    col.find_one.return_value = _doc()
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        assert jr.JobRepository().find_one("u1", "acme.io").domaine == "acme.io"
    col.find_one.return_value = None
    with patch.object(jr, "get_db", return_value=_db_with(col)):
        assert jr.JobRepository().find_one("u1", "ghost.io") is None

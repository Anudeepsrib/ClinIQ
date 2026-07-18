from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.security.auth import create_access_token, user_db
from main import app

client = TestClient(app)


def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            JWT_SECRET_KEY="dev-secret-change-in-production",
            CORS_ALLOWED_ORIGINS="https://cliniq.example.com",
        )


def _token_for(username: str, role: str = "viewer", departments: list[str] | None = None) -> str:
    departments = departments or ["general"]
    try:
        user_db.create_user(
            username=username,
            password="local-test-password",
            role=role,
            departments=departments,
            full_name="Test User",
        )
    except ValueError:
        pass
    return create_access_token({"sub": username, "role": role, "departments": departments})


def test_query_requires_authentication():
    response = client.post("/api/v1/query", json={"question": "MRI policy"})
    assert response.status_code == 401


def test_query_rejects_wrong_department_access():
    token = _token_for("dept_scope_user", departments=["general"])
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "MRI policy", "departments": ["radiology"]},
    )
    assert response.status_code == 403


def test_upload_rejects_path_traversal_filename():
    token = _token_for("upload_scope_user", departments=["general"])
    response = client.post(
        "/api/v1/ingest",
        headers={"Authorization": f"Bearer {token}"},
        data={"department": "general"},
        files={"file": ("../evil.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_returns_upsert_contract():
    token = _token_for("upsert_contract_user", departments=["general"])
    result = {
        "doc_id": "general_policy.pdf",
        "filename": "policy.pdf",
        "department": "general",
        "change_type": "new",
        "version": 1,
        "chunk_count": 2,
        "content_hash": "abc123",
    }

    with patch("app.api.routes.upsert_document", new=AsyncMock(return_value=result)):
        response = client.post(
            "/api/v1/ingest",
            headers={"Authorization": f"Bearer {token}"},
            data={"department": "general"},
            files={"file": ("policy.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["change_type"] == "new"
    assert response.json()["chunk_count"] == 2
    assert "chunks_count" not in response.json()


def test_async_upload_job_completes_and_is_owner_scoped():
    token = _token_for("async_ingest_user", departments=["general"])
    other_token = _token_for("async_ingest_other", departments=["general"])
    result = {
        "doc_id": "general_policy.pdf",
        "filename": "policy.pdf",
        "department": "general",
        "change_type": "new",
        "version": 1,
        "chunk_count": 2,
        "content_hash": "abc123",
    }

    with patch("app.api.routes.upsert_document", new=AsyncMock(return_value=result)):
        response = client.post(
            "/api/v1/ingest/jobs",
            headers={"Authorization": f"Bearer {token}"},
            data={"department": "general"},
            files={"file": ("policy.pdf", b"%PDF-1.4", "application/pdf")},
        )

    assert response.status_code == 202
    assert response.json()["modality"] == "document"
    job_id = response.json()["job_id"]
    status_response = client.get(
        f"/api/v1/ingest/jobs/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["result"]["chunk_count"] == 2
    assert client.get(
        f"/api/v1/ingest/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    ).status_code == 404


def test_query_masks_phi_before_graph_invocation():
    token = _token_for("phi_scope_user", departments=["general"])
    captured_inputs = {}

    async def fake_ainvoke(inputs, config=None):
        captured_inputs.update(inputs)
        return {
            "generation": "No relevant documents found.",
            "documents": [],
            "hallucination_score": "yes",
        }

    with patch("app.api.routes.app_graph.ainvoke", new=AsyncMock(side_effect=fake_ainvoke)):
        response = client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question": "What policy applies to John Doe, phone 555-123-4567?",
                "departments": ["general"],
            },
        )

    assert response.status_code == 200
    assert "John Doe" not in captured_inputs["question"]
    assert "555-123-4567" not in captured_inputs["question"]
    assert "<PERSON_" in captured_inputs["question"]
    assert "<PHONE_NUMBER_" in captured_inputs["question"]


def test_query_returns_feedback_run_id_when_tracing_is_enabled():
    token = _token_for("feedback_run_user", departments=["general"])

    async def fake_ainvoke(inputs, config=None):
        assert config.get("run_id") is not None
        return {"generation": "Policy answer", "documents": [], "hallucination_score": "yes"}

    with (
        patch.object(settings, "ENABLE_EXTERNAL_TRACING", True),
        patch("app.api.routes.app_graph.ainvoke", new=AsyncMock(side_effect=fake_ainvoke)),
    ):
        response = client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"question": "What is the policy?", "departments": ["general"]},
        )

    assert response.status_code == 200
    assert response.json()["feedback_enabled"] is True
    assert response.json()["run_id"]


def test_feedback_masks_phi_like_comment_before_external_tracing():
    token = _token_for("feedback_mask_user", role="nurse", departments=["general"])

    with patch("app.api.routes.ls_create_feedback", return_value=True) as create_feedback:
        response = client.post(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "run_id": "11111111-1111-1111-1111-111111111111",
                "score": 0,
                "comment": "Call John Doe at 555-123-4567",
            },
        )

    assert response.status_code == 200
    assert "John Doe" not in create_feedback.call_args.kwargs["comment"]
    assert "555-123-4567" not in create_feedback.call_args.kwargs["comment"]

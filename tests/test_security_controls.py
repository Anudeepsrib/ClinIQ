from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
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

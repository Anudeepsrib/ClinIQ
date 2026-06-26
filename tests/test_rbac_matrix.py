import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.security.auth import create_access_token, user_db
from main import app

MATRIX_PATH = Path(__file__).parent / "evaluation" / "rbac_test_matrix.json"
PASSWORD = "local-test-password"
client = TestClient(app)


def _matrix_personas() -> list[dict]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))["personas"]


def _token_for(persona: dict) -> str:
    username = f"matrix_{persona['id']}_{uuid.uuid4().hex[:8]}"
    user_db.create_user(
        username=username,
        password=PASSWORD,
        role=persona["role"],
        departments=persona["departments"],
        full_name=persona["display_name"],
    )
    return create_access_token(
        {
            "sub": username,
            "role": persona["role"],
            "departments": persona["departments"],
        }
    )


@pytest.mark.parametrize("persona", _matrix_personas(), ids=lambda item: item["id"])
def test_persona_department_scope_matches_matrix(persona):
    token = _token_for(persona)
    response = client.get("/api/v1/departments", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["role"] == persona["role"]

    expected_departments = (
        set(settings.departments_list)
        if persona["role"] == "admin"
        else set(persona["departments"])
    )
    assert set(body["departments"]) == expected_departments


@pytest.mark.parametrize("persona", _matrix_personas(), ids=lambda item: item["id"])
def test_query_access_follows_rbac_matrix(persona):
    token = _token_for(persona)
    captured_inputs = []

    async def fake_ainvoke(inputs, config=None):
        captured_inputs.append(inputs)
        return {
            "generation": "Synthetic policy answer.",
            "documents": [],
            "hallucination_score": "yes",
        }

    with patch("app.api.routes.app_graph.ainvoke", new=AsyncMock(side_effect=fake_ainvoke)):
        allowed_department = persona["query_allow"][0]
        allowed_response = client.post(
            "/api/v1/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"question": "What is the policy?", "departments": [allowed_department]},
        )
        assert allowed_response.status_code == 200
        assert captured_inputs[-1]["departments"] == [allowed_department]

        if persona["query_deny"]:
            denied_department = persona["query_deny"][0]
            denied_response = client.post(
                "/api/v1/query",
                headers={"Authorization": f"Bearer {token}"},
                json={"question": "What is the policy?", "departments": [denied_department]},
            )
            assert denied_response.status_code == 403


@pytest.mark.parametrize("persona", _matrix_personas(), ids=lambda item: item["id"])
def test_admin_endpoint_access_follows_rbac_matrix(persona):
    token = _token_for(persona)
    response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})

    expected_status = 200 if persona["admin_endpoints_allowed"] else 403
    assert response.status_code == expected_status

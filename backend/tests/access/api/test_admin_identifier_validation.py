import unittest
from collections.abc import Callable
from typing import cast
from uuid import UUID

from access.adapters.http.admin_router import AdminUseCases, create_admin_router
from access.application.authorize_action import AuthorizeAction
from access.domain.errors import (
    AccessPresetNotFound,
    AccessScopeNotFound,
    AccessUserNotFound,
)
from bootstrap.http_error_handlers import register_exception_handlers
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from shared.identity import AuthenticatedIdentity


class _RoleRepository:
    def __init__(self):
        self.calls: list[str] = []

    def find_by_id(self, role_id: str):
        self.calls.append(role_id)
        UUID(role_id)


class _AllowAdmin:
    def execute(self, **kwargs: object) -> None:
        return None


class _UserRepository:
    def find_by_subject(self, subject: str) -> "_AccessUser":
        return _AccessUser()


class _AccessUser:
    user_id: str = "user-1"


class _Identity:
    def generate_operation_id(self) -> str:
        return "op-1"


class _MissingAccessUser:
    def execute(self, **kwargs: object) -> None:
        raise AccessUserNotFound()


class _MissingRolePreset:
    def execute(self, **kwargs: object) -> None:
        raise AccessPresetNotFound()


class _MissingScope:
    def execute(self, *args: object, **kwargs: object) -> None:
        raise AccessScopeNotFound()


class _AdminUseCasesDouble:
    def __init__(self, role_repository: _RoleRepository) -> None:
        self.role_repository = role_repository
        self.user_repository = _UserRepository()
        self.identity = _Identity()
        self.get_access_user = _MissingAccessUser()
        self.get_role_preset = _MissingRolePreset()
        self.activate_scope = _MissingScope()
        self.deactivate_scope = _MissingScope()


def _build_client() -> tuple[TestClient, _RoleRepository]:
    role_repository = _RoleRepository()

    def identity_resolver() -> AuthenticatedIdentity:
        return AuthenticatedIdentity(subject="admin-subject", session_id="session-1")

    def authorize_action_provider() -> _AllowAdmin:
        return _AllowAdmin()

    def admin_use_case_provider() -> AdminUseCases:
        return cast(AdminUseCases, _AdminUseCasesDouble(role_repository))

    app = FastAPI()
    register_exception_handlers(app)
    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(
        create_admin_router(
            identity_resolver,
            cast(Callable[..., AuthorizeAction], authorize_action_provider),
            admin_use_case_provider,
        )
    )
    app.include_router(api_router)

    return TestClient(app, raise_server_exceptions=False), role_repository


class TestAdminIdentifierValidation(unittest.TestCase):
    def test_get_role_rejects_invalid_uuid_before_repository_lookup(self):
        client, role_repository = _build_client()

        response = client.get("/api/v1/access/roles/not-a-valid-uuid")

        self.assertEqual(response.status_code, 422)
        body = response.json()["error"]
        self.assertEqual(body["code"], "request_validation_error")
        self.assertIn("path.role_id", {field["path"] for field in body["fields"]})
        self.assertEqual(role_repository.calls, [])

    def test_get_role_keeps_not_found_for_valid_missing_uuid(self):
        client, role_repository = _build_client()
        role_id = "00000000-0000-0000-0000-000000000001"

        response = client.get(f"/api/v1/access/roles/{role_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "access_role_not_found"})
        self.assertEqual(role_repository.calls, [role_id])

    def test_other_identifier_families_reject_invalid_uuid(self):
        client, _ = _build_client()
        cases = [
            ("GET", "/api/v1/access/users/not-a-valid-uuid", None, "user_id"),
            ("GET", "/api/v1/access/role-presets/not-a-valid-uuid", None, "preset_id"),
            (
                "PATCH",
                "/api/v1/access/scopes/not-a-valid-uuid/status",
                {"is_active": True, "expected_version": 1, "reason": "Validation test"},
                "scope_id",
            ),
        ]

        for method, path, payload, identifier_name in cases:
            with self.subTest(identifier=identifier_name):
                response = client.request(method, path, json=payload)

                self.assertEqual(response.status_code, 422)
                body = response.json()["error"]
                self.assertEqual(body["code"], "request_validation_error")
                self.assertIn(
                    f"path.{identifier_name}",
                    {field["path"] for field in body["fields"]},
                )

    def test_get_user_keeps_not_found_for_valid_missing_uuid(self):
        client, _ = _build_client()
        user_id = "00000000-0000-0000-0000-000000000002"

        response = client.get(f"/api/v1/access/users/{user_id}")

        self.assertEqual(response.status_code, 404)
        body = response.json()["error"]
        self.assertEqual(body["code"], "access_user_not_found")

    def test_get_role_preset_keeps_not_found_for_valid_missing_uuid(self):
        client, _ = _build_client()
        preset_id = "00000000-0000-0000-0000-000000000003"

        response = client.get(f"/api/v1/access/role-presets/{preset_id}")

        self.assertEqual(response.status_code, 404)
        body = response.json()["error"]
        self.assertEqual(body["code"], "access_preset_not_found")

    def test_change_scope_status_keeps_not_found_for_valid_missing_uuid(self):
        client, _ = _build_client()
        scope_id = "00000000-0000-0000-0000-000000000004"

        response = client.patch(
            f"/api/v1/access/scopes/{scope_id}/status",
            json={
                "is_active": True,
                "expected_version": 1,
                "reason": "Validation test",
            },
        )

        self.assertEqual(response.status_code, 404)
        body = response.json()["error"]
        self.assertEqual(body["code"], "access_scope_not_found")


if __name__ == "__main__":
    unittest.main()

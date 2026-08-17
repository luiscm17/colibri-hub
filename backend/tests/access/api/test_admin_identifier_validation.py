import unittest
from collections.abc import Callable
from typing import cast
from uuid import UUID

from access.adapters.http.admin_router import AdminUseCases, create_admin_router
from access.application.authorize_action import AuthorizeAction
from access.domain.errors import (
    AccessError,
    AccessPresetNotFound,
    AccessRoleNotFound,
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

    def find_by_id(self, user_id: str) -> None:
        return None


class _AccessUser:
    user_id: str = "user-1"


class _Identity:
    def generate_operation_id(self) -> str:
        return "op-1"


class _MissingUseCase:
    def __init__(self, error_type: type[AccessError]) -> None:
        self._error_type = error_type

    def execute(self, *args: object, **kwargs: object) -> None:
        raise self._error_type()


class _AdminUseCasesDouble:
    def __init__(self, role_repository: _RoleRepository) -> None:
        self.role_repository = role_repository
        self.user_repository = _UserRepository()
        self.identity = _Identity()

        missing_user = _MissingUseCase(AccessUserNotFound)
        missing_role = _MissingUseCase(AccessRoleNotFound)
        missing_preset = _MissingUseCase(AccessPresetNotFound)
        missing_scope = _MissingUseCase(AccessScopeNotFound)

        self.get_access_user = missing_user
        self.replace_user_roles = missing_user
        self.preview_user_role_replacement = missing_user

        self.get_role_preset = missing_preset
        self.update_role_preset = missing_preset
        self.change_role_preset_status = missing_preset
        self.create_role_from_preset = missing_preset

        self.update_role = missing_role
        self.preview_role_change = missing_role
        self.activate_role = missing_role
        self.deactivate_role = missing_role

        self.activate_scope = missing_scope
        self.deactivate_scope = missing_scope


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

    def test_every_admin_path_binding_rejects_malformed_uuid(self):
        cases = (
            (
                "PUT",
                "/api/v1/access/users/not-a-valid-uuid/roles",
                {
                    "role_ids": ["00000000-0000-0000-0000-000000000001"],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "user_id",
            ),
            (
                "POST",
                "/api/v1/access/users/not-a-valid-uuid/roles/preview",
                {"role_ids": ["00000000-0000-0000-0000-000000000001"]},
                "user_id",
            ),
            ("GET", "/api/v1/access/users/not-a-valid-uuid", None, "user_id"),
            (
                "PATCH",
                "/api/v1/access/users/not-a-valid-uuid/status",
                {"is_active": True, "expected_version": 1, "reason": "validation test"},
                "user_id",
            ),
            ("GET", "/api/v1/access/roles/not-a-valid-uuid", None, "role_id"),
            (
                "PUT",
                "/api/v1/access/roles/not-a-valid-uuid",
                {
                    "role_name": "Role Name",
                    "description": "Role description",
                    "permissions": [],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "role_id",
            ),
            (
                "POST",
                "/api/v1/access/roles/not-a-valid-uuid/preview",
                {"permissions": []},
                "role_id",
            ),
            (
                "PATCH",
                "/api/v1/access/roles/not-a-valid-uuid/status",
                {"is_active": True, "expected_version": 1, "reason": "validation test"},
                "role_id",
            ),
            ("GET", "/api/v1/access/role-presets/not-a-valid-uuid", None, "preset_id"),
            (
                "PUT",
                "/api/v1/access/role-presets/not-a-valid-uuid",
                {
                    "preset_name": "Preset Name",
                    "description": "Preset description",
                    "permissions": [],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "preset_id",
            ),
            (
                "PATCH",
                "/api/v1/access/role-presets/not-a-valid-uuid/status",
                {"is_active": True, "expected_version": 1, "reason": "validation test"},
                "preset_id",
            ),
            (
                "POST",
                "/api/v1/access/role-presets/not-a-valid-uuid/roles",
                {
                    "role_code": "role-code",
                    "role_name": "Role Name",
                    "description": "Role description",
                    "reason": "validation test",
                },
                "preset_id",
            ),
            (
                "PATCH",
                "/api/v1/access/scopes/not-a-valid-uuid/status",
                {"is_active": True, "expected_version": 1, "reason": "validation test"},
                "scope_id",
            ),
        )

        for method, path, payload, identifier_name in cases:
            with self.subTest(method=method, path=path):
                client, _ = _build_client()
                response = client.request(method, path, json=payload)

                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    response.json()["error"]["code"], "request_validation_error"
                )
                field_paths = {
                    field["path"] for field in response.json()["error"]["fields"]
                }
                self.assertIn(f"path.{identifier_name}", field_paths)

    def test_every_admin_path_binding_keeps_not_found_for_valid_missing_uuid(self):
        missing_id = "00000000-0000-0000-0000-000000000099"
        status_body = {
            "is_active": True,
            "expected_version": 1,
            "reason": "validation test",
        }
        cases = (
            (
                "PUT",
                f"/api/v1/access/users/{missing_id}/roles",
                {
                    "role_ids": ["00000000-0000-0000-0000-000000000001"],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "error",
                "access_user_not_found",
            ),
            (
                "POST",
                f"/api/v1/access/users/{missing_id}/roles/preview",
                {"role_ids": ["00000000-0000-0000-0000-000000000001"]},
                "error",
                "access_user_not_found",
            ),
            (
                "GET",
                f"/api/v1/access/users/{missing_id}",
                None,
                "error",
                "access_user_not_found",
            ),
            (
                "PATCH",
                f"/api/v1/access/users/{missing_id}/status",
                status_body,
                "detail",
                "access_user_not_found",
            ),
            (
                "GET",
                f"/api/v1/access/roles/{missing_id}",
                None,
                "detail",
                "access_role_not_found",
            ),
            (
                "PUT",
                f"/api/v1/access/roles/{missing_id}",
                {
                    "role_name": "Role Name",
                    "description": "Role description",
                    "permissions": [],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "error",
                "access_role_not_found",
            ),
            (
                "POST",
                f"/api/v1/access/roles/{missing_id}/preview",
                {"permissions": []},
                "error",
                "access_role_not_found",
            ),
            (
                "PATCH",
                f"/api/v1/access/roles/{missing_id}/status",
                status_body,
                "error",
                "access_role_not_found",
            ),
            (
                "GET",
                f"/api/v1/access/role-presets/{missing_id}",
                None,
                "error",
                "access_preset_not_found",
            ),
            (
                "PUT",
                f"/api/v1/access/role-presets/{missing_id}",
                {
                    "preset_name": "Preset Name",
                    "description": "Preset description",
                    "permissions": [],
                    "expected_version": 1,
                    "reason": "validation test",
                },
                "error",
                "access_preset_not_found",
            ),
            (
                "PATCH",
                f"/api/v1/access/role-presets/{missing_id}/status",
                status_body,
                "error",
                "access_preset_not_found",
            ),
            (
                "POST",
                f"/api/v1/access/role-presets/{missing_id}/roles",
                {
                    "role_code": "role-code",
                    "role_name": "Role Name",
                    "description": "Role description",
                    "reason": "validation test",
                },
                "error",
                "access_preset_not_found",
            ),
            (
                "PATCH",
                f"/api/v1/access/scopes/{missing_id}/status",
                status_body,
                "error",
                "access_scope_not_found",
            ),
        )

        for method, path, payload, shape, expected_code in cases:
            with self.subTest(method=method, path=path):
                client, _ = _build_client()
                response = client.request(method, path, json=payload)

                self.assertEqual(response.status_code, 404)
                if shape == "detail":
                    self.assertEqual(response.json(), {"detail": expected_code})
                else:
                    self.assertEqual(response.json()["error"]["code"], expected_code)

    def test_get_role_keeps_not_found_for_valid_missing_uuid(self):
        client, role_repository = _build_client()
        role_id = "00000000-0000-0000-0000-000000000001"

        response = client.get(f"/api/v1/access/roles/{role_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "access_role_not_found"})
        self.assertEqual(role_repository.calls, [role_id])


if __name__ == "__main__":
    unittest.main()

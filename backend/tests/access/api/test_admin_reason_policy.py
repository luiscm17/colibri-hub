import unittest

from access.adapters.http.models import (
    AuditEntryResponse,
    CreateRoleFromPresetRequest,
    CreateRolePresetRequest,
    CreateRoleRequest,
    RegisterScopeRequest,
    ReplaceUserRolesRequest,
    StatusChangeRequest,
    UpdateRolePresetRequest,
    UpdateRoleRequest,
)


class AdministrativeReasonModelTests(unittest.TestCase):
    def _assert_normalizes_reason(self, build_request) -> None:
        cases = (
            ("omitted", {}, None),
            ("explicit null", {"reason": None}, None),
            ("empty", {"reason": ""}, None),
            ("whitespace", {"reason": "  \t  "}, None),
            (
                "trimmed text",
                {"reason": "  planned access update  "},
                "planned access update",
            ),
        )

        for name, reason_payload, expected in cases:
            with self.subTest(name=name):
                request = build_request(reason_payload)
                self.assertEqual(request.reason, expected)

    def test_create_role_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: CreateRoleRequest(
                role_code="reader",
                role_name="Reader",
                permissions=[],
                **reason,
            )
        )

    def test_update_role_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: UpdateRoleRequest(
                role_name="Reader",
                permissions=[],
                expected_version=1,
                **reason,
            )
        )

    def test_status_change_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: StatusChangeRequest(
                is_active=True,
                expected_version=1,
                **reason,
            )
        )

    def test_replace_user_role_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: ReplaceUserRolesRequest(
                role_ids=["role-1"],
                expected_version=1,
                **reason,
            )
        )

    def test_register_scope_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: RegisterScopeRequest(
                definition_key="warehouse.raw_materials",
                **reason,
            )
        )

    def test_create_role_preset_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: CreateRolePresetRequest(
                preset_code="warehouse_reader",
                preset_name="Warehouse Reader",
                permissions=[],
                **reason,
            )
        )

    def test_update_role_preset_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: UpdateRolePresetRequest(
                preset_name="Warehouse Reader",
                permissions=[],
                expected_version=1,
                **reason,
            )
        )

    def test_create_role_from_preset_reason(self) -> None:
        self._assert_normalizes_reason(
            lambda reason: CreateRoleFromPresetRequest(
                role_code="warehouse_reader",
                role_name="Warehouse Reader",
                **reason,
            )
        )

    def test_audit_response_preserves_historical_absent_or_empty_reason(self) -> None:
        for reason in (None, ""):
            with self.subTest(reason=reason):
                response = AuditEntryResponse(
                    audit_id="audit-1",
                    operation_id="operation-1",
                    change_kind="user_roles_replaced",
                    subject_type="user",
                    subject_id="user-1",
                    performed_by_user_id="admin-1",
                    reason=reason,
                    occurred_at="2026-08-18T12:00:00+00:00",
                )

                self.assertEqual(response.reason, reason)

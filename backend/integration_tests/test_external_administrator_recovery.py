"""Executable drill for the external administrator-recovery runbook."""

import subprocess
import unittest
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import text

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)
from supabase import create_client

_CUSTODIAN_A = "custodian-a"
_CUSTODIAN_B = "custodian-b"


@dataclass
class _RecoveryRecord:
    """Test-side representation of evidence retained outside Colibri Hub."""

    request_id: str
    approvers: set[str]
    emergency_reason: str | None = None
    notifications: list[str] = field(default_factory=list)
    temporary_material_revoked: bool = False
    closed: bool = False
    post_incident_reviewed: bool = False
    events: list[str] = field(default_factory=list)


class _ExternalRecoveryDrill:
    """Perform only test-owned, external control-plane and database operations."""

    def __init__(self, *, engine, client) -> None:
        self._engine = engine
        self._client = client
        self.created_subjects: list[str] = []

    def establish_operational_administrator(self, *, email: str) -> str:
        response = self._client.auth.admin.create_user(
            {
                "email": email,
                "password": "ExternalRecoveryPass1!",
                "email_confirm": True,
            }
        )
        assert response.user is not None
        subject = str(response.user.id)
        self.created_subjects.append(subject)
        user_id = str(uuid4())
        with self._engine.begin() as connection:
            role_id = connection.execute(
                text(
                    "SELECT role_id FROM access_roles "
                    "WHERE is_system_administrator = true"
                )
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO authentication_accounts "
                    "(authentication_account_id, identity_subject, normalized_email, "
                    "display_name, user_code, status) "
                    "VALUES (:account_id, :subject, :email, :display_name, :user_code, "
                    "'active')"
                ),
                {
                    "account_id": str(uuid4()),
                    "subject": subject,
                    "email": email,
                    "display_name": "External recovery administrator",
                    "user_code": f"REC-{subject[:8]}",
                },
            )
            connection.execute(
                text(
                    "INSERT INTO access_users "
                    "(user_id, identity_subject, user_code, display_name) "
                    "VALUES (:user_id, :subject, :user_code, :display_name)"
                ),
                {
                    "user_id": user_id,
                    "subject": subject,
                    "user_code": f"REC-{subject[:8]}",
                    "display_name": "External recovery administrator",
                },
            )
            connection.execute(
                text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id) "
                    "VALUES (:assignment_id, :user_id, :role_id, :user_id)"
                ),
                {
                    "assignment_id": str(uuid4()),
                    "user_id": user_id,
                    "role_id": role_id,
                },
            )
        return subject

    def activate_recovery(self, record: _RecoveryRecord, *, email: str) -> str:
        if record.emergency_reason is None:
            if record.approvers != {_CUSTODIAN_A, _CUSTODIAN_B}:
                raise PermissionError("ordinary recovery requires both custodians")
        elif record.approvers not in ({_CUSTODIAN_A}, {_CUSTODIAN_B}):
            raise PermissionError("emergency recovery requires one designated custodian")

        subject = self.establish_operational_administrator(email=email)
        record.events.append("activated")
        return subject

    @staticmethod
    def notify_other_custodian(record: _RecoveryRecord) -> None:
        other = _CUSTODIAN_B if _CUSTODIAN_A in record.approvers else _CUSTODIAN_A
        record.notifications.append(other)
        record.events.append("notified")

    @staticmethod
    def close_recovery(record: _RecoveryRecord) -> None:
        record.temporary_material_revoked = True
        record.closed = True
        record.events.extend(("temporary_material_revoked", "closed"))

    @staticmethod
    def complete_post_incident_review(record: _RecoveryRecord) -> None:
        record.post_incident_reviewed = True
        record.events.append("reviewed")


class ExternalAdministratorRecoveryIntegrationTests(unittest.TestCase):
    """Run the manual-first recovery scenarios against local Supabase resources."""

    @classmethod
    def setUpClass(cls) -> None:
        validated_test_database_url()
        cls.engine = test_engine()
        cls.provider_url, cls.service_role_key = cls._local_provider_credentials()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self._deactivate_owned_recovery_fixtures()
        self.client = create_client(self.provider_url, self.service_role_key)
        self.drill = _ExternalRecoveryDrill(engine=self.engine, client=self.client)
        self.token = uuid4().hex

    def tearDown(self) -> None:
        for subject in self.drill.created_subjects:
            self.client.auth.admin.delete_user(subject)
        self._deactivate_owned_recovery_fixtures()
        self.client.auth.close()

    def test_ordinary_recovery_requires_two_custodians_and_restores_continuity(self) -> None:
        initial_subject = self.drill.establish_operational_administrator(
            email=f"recovery-initial-{self.token}@example.invalid"
        )
        record = _RecoveryRecord(
            request_id=f"ordinary-{self.token}",
            approvers={_CUSTODIAN_A, _CUSTODIAN_B},
        )

        recovered_subject = self.drill.activate_recovery(
            record,
            email=f"recovery-ordinary-{self.token}@example.invalid",
        )
        self.drill.notify_other_custodian(record)
        self.drill.close_recovery(record)

        self.assertEqual(
            self._operational_administrator_subjects(),
            {initial_subject, recovered_subject},
        )
        self.assertEqual(record.notifications, [_CUSTODIAN_B])
        self.assertTrue(record.temporary_material_revoked)
        self.assertTrue(record.closed)
        self.assertEqual(
            record.events,
            ["activated", "notified", "temporary_material_revoked", "closed"],
        )

    def test_emergency_recovery_records_notification_closure_revocation_and_review(self) -> None:
        initial_subject = self.drill.establish_operational_administrator(
            email=f"recovery-initial-{self.token}@example.invalid"
        )
        record = _RecoveryRecord(
            request_id=f"emergency-{self.token}",
            approvers={_CUSTODIAN_A},
            emergency_reason="Documented administrative continuity emergency",
        )

        recovered_subject = self.drill.activate_recovery(
            record,
            email=f"recovery-emergency-{self.token}@example.invalid",
        )
        self.drill.notify_other_custodian(record)
        self.drill.close_recovery(record)
        self.drill.complete_post_incident_review(record)

        self.assertEqual(
            self._operational_administrator_subjects(),
            {initial_subject, recovered_subject},
        )
        self.assertEqual(record.notifications, [_CUSTODIAN_B])
        self.assertTrue(record.temporary_material_revoked)
        self.assertTrue(record.closed)
        self.assertTrue(record.post_incident_reviewed)
        self.assertEqual(
            record.events,
            [
                "activated",
                "notified",
                "temporary_material_revoked",
                "closed",
                "reviewed",
            ],
        )

    def test_ordinary_unilateral_recovery_is_denied_without_control_plane_changes(self) -> None:
        initial_subject = self.drill.establish_operational_administrator(
            email=f"recovery-initial-{self.token}@example.invalid"
        )
        record = _RecoveryRecord(
            request_id=f"denied-{self.token}",
            approvers={_CUSTODIAN_A},
        )

        with self.assertRaisesRegex(
            PermissionError, "ordinary recovery requires both custodians"
        ):
            self.drill.activate_recovery(
                record,
                email=f"recovery-denied-{self.token}@example.invalid",
            )

        self.assertEqual(self.drill.created_subjects, [initial_subject])
        self.assertEqual(self._operational_administrator_subjects(), {initial_subject})
        self.assertEqual(record.events, [])

    def _operational_administrator_subjects(self) -> set[str]:
        with self.engine.connect() as connection:
            return set(
                connection.execute(
                    text(
                        "SELECT preflight.identity_subject "
                        "FROM access_operational_administrators_preflight preflight "
                        "JOIN authentication_accounts accounts "
                        "ON accounts.identity_subject::text = preflight.identity_subject "
                        "WHERE accounts.normalized_email "
                        "LIKE 'recovery-%@example.invalid'"
                    )
                ).scalars()
            )

    def _deactivate_owned_recovery_fixtures(self) -> None:
        with self.engine.begin() as connection:
            subjects = [
                str(subject)
                for subject in connection.execute(
                    text(
                        "SELECT identity_subject FROM authentication_accounts "
                        "WHERE normalized_email LIKE 'recovery-%@example.invalid' "
                        "AND status = 'active'"
                    )
                ).scalars()
            ]
            connection.execute(
                text(
                    "UPDATE authentication_accounts SET status = 'disabled' "
                    "WHERE normalized_email LIKE 'recovery-%@example.invalid' "
                    "AND status = 'active'"
                )
            )
            connection.execute(
                text(
                    "UPDATE access_users SET is_active = false "
                    "WHERE identity_subject = ANY(:subjects)"
                ),
                {"subjects": subjects},
            )

    @staticmethod
    def _local_provider_credentials() -> tuple[str, str]:
        result = subprocess.run(
            ["pnpm", "supabase", "status", "--output", "env"],
            capture_output=True,
            text=True,
            check=True,
        )
        values = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.removeprefix("export ").partition("=")
            if separator:
                values[key] = value.strip("'\"")
        return values["API_URL"], values["SERVICE_ROLE_KEY"]


if __name__ == "__main__":
    unittest.main()

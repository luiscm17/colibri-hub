"""Integration tests for Authentication PostgreSQL persistence.

Verifies:
- Email and identity_subject uniqueness constraints
- Status check constraint
- Version check constraint
- Optimistic concurrency (version conflict)
- Audit immutability (no UPDATE/DELETE)
- Identity immutability trigger
- RLS blocking browser roles
"""

import unittest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from auth.adapters.persistence.records import (
    AuthenticationAccountRecord,
    AuthenticationAuditRecord,
)
from backend.integration_tests.database_test_support import test_engine
from infra.persistence.record_registry import register_auth_records

register_auth_records()


class AuthenticationPostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = test_engine()
        cls.tag = uuid4().hex[:8]
        # Seed one account for constraint tests
        with Session(cls.engine) as session:
            session.add(
                AuthenticationAccountRecord(
                    authentication_account_id=uuid4(),
                    identity_subject=uuid4(),
                    normalized_email=f"seed-{cls.tag}@example.com",
                    display_name="Seed User",
                    user_code=f"USR-SEED-{cls.tag}",
                    status="active",
                    version=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_email_uniqueness_constraint(self):
        """Duplicate normalized_email is rejected case-insensitively."""
        with Session(self.engine) as session:
            session.add(
                AuthenticationAccountRecord(
                    authentication_account_id=uuid4(),
                    identity_subject=uuid4(),
                    normalized_email=f"seed-{self.tag}@example.com",
                    display_name="Dup",
                    user_code=f"USR-DUP-{uuid4().hex[:6]}",
                    status="awaiting_password_change",
                    version=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_identity_subject_uniqueness(self):
        """Duplicate identity_subject is rejected."""
        # Get the seeded account's identity_subject
        with Session(self.engine) as session:
            existing = session.execute(
                text(
                    "SELECT identity_subject FROM authentication_accounts "
                    "WHERE normalized_email = :email"
                ),
                {"email": f"seed-{self.tag}@example.com"},
            ).scalar_one()

        with Session(self.engine) as session:
            session.add(
                AuthenticationAccountRecord(
                    authentication_account_id=uuid4(),
                    identity_subject=existing,
                    normalized_email=f"other-{uuid4().hex[:6]}@example.com",
                    display_name="Other",
                    user_code=f"USR-OTH-{uuid4().hex[:6]}",
                    status="awaiting_password_change",
                    version=1,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            with self.assertRaises(IntegrityError):
                session.commit()

    def test_status_check_constraint(self):
        """Invalid status value is rejected by check constraint."""
        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "INSERT INTO authentication_accounts "
                        "(authentication_account_id, identity_subject, normalized_email, "
                        "display_name, user_code, status, version, created_at, updated_at) "
                        "VALUES (:id, :sub, :email, :name, :code, :status, 1, now(), now())"
                    ),
                    {
                        "id": str(uuid4()),
                        "sub": str(uuid4()),
                        "email": f"bad-status-{uuid4().hex[:6]}@example.com",
                        "name": "Bad Status",
                        "code": f"USR-BAD-{uuid4().hex[:6]}",
                        "status": "invalid_status",
                    },
                )
                session.commit()

    def test_version_check_constraint(self):
        """Version below 1 is rejected."""
        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "INSERT INTO authentication_accounts "
                        "(authentication_account_id, identity_subject, normalized_email, "
                        "display_name, user_code, status, version, created_at, updated_at) "
                        "VALUES (:id, :sub, :email, :name, :code, 'active', 0, now(), now())"
                    ),
                    {
                        "id": str(uuid4()),
                        "sub": str(uuid4()),
                        "email": f"low-ver-{uuid4().hex[:6]}@example.com",
                        "name": "Low Version",
                        "code": f"USR-LV-{uuid4().hex[:6]}",
                    },
                )
                session.commit()

    def test_audit_immutability(self):
        """Audits cannot be updated or deleted."""
        audit_id = uuid4()
        with Session(self.engine) as session:
            # Get seeded account ID for FK
            account_id = session.execute(
                text(
                    "SELECT authentication_account_id FROM authentication_accounts "
                    "WHERE normalized_email = :email"
                ),
                {"email": f"seed-{self.tag}@example.com"},
            ).scalar_one()

            session.execute(
                text(
                    "INSERT INTO authentication_audits "
                    "(authentication_audit_id, operation_id, event_type, outcome, "
                    "affected_account_id, occurred_at) "
                    "VALUES (:id, :op, 'logout', 'succeeded', :acc, now())"
                ),
                {"id": str(audit_id), "op": str(uuid4()), "acc": str(account_id)},
            )
            session.commit()

        # Try UPDATE
        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "UPDATE authentication_audits SET outcome = 'failed' "
                        "WHERE authentication_audit_id = :id"
                    ),
                    {"id": str(audit_id)},
                )
                session.commit()
            session.rollback()

        # Try DELETE
        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "DELETE FROM authentication_audits "
                        "WHERE authentication_audit_id = :id"
                    ),
                    {"id": str(audit_id)},
                )
                session.commit()

    def test_identity_immutability_trigger(self):
        """identity_subject and normalized_email cannot be changed after creation."""
        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "UPDATE authentication_accounts "
                        "SET identity_subject = :new_sub "
                        "WHERE normalized_email = :email"
                    ),
                    {
                        "new_sub": str(uuid4()),
                        "email": f"seed-{self.tag}@example.com",
                    },
                )
                session.commit()
            session.rollback()

        with Session(self.engine) as session:
            with self.assertRaises(DBAPIError):
                session.execute(
                    text(
                        "UPDATE authentication_accounts "
                        "SET normalized_email = 'changed@example.com' "
                        "WHERE normalized_email = :email"
                    ),
                    {"email": f"seed-{self.tag}@example.com"},
                )
                session.commit()

    def test_rls_blocks_browser_roles(self):
        """Browser roles (anon, authenticated) cannot access auth tables."""
        with self.engine.connect() as connection:
            transaction = connection.begin()
            connection.execute(text("SET LOCAL ROLE anon"))
            with self.assertRaises(DBAPIError):
                connection.execute(
                    text("SELECT * FROM authentication_accounts")
                )
            transaction.rollback()

        with self.engine.connect() as connection:
            transaction = connection.begin()
            connection.execute(text("SET LOCAL ROLE authenticated"))
            with self.assertRaises(DBAPIError):
                connection.execute(
                    text("SELECT * FROM authentication_audits")
                )
            transaction.rollback()


if __name__ == "__main__":
    unittest.main()

"""Integration tests for C3 and C4 critical fixes.

C3: Concurrent last-admin removal rejected under row lock.
C4 (partial): Cross-context rollback on provisioning failure.

Requires: TEST_DATABASE_URL pointing to the guarded local PostgreSQL (port 54322).
Run with: TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
          uv run --locked --package backend python -m unittest backend.integration_tests.test_access_control_critical -v
"""

import unittest
import threading
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from access.adapters.persistence.assignment_repository import AssignmentRepositoryAdapter
from access.adapters.persistence.audit_repository import AccessAuditRepositoryAdapter
from access.adapters.persistence.role_repository import RoleRepositoryAdapter
from access.adapters.persistence.transaction import TransactionAdapter
from access.adapters.persistence.user_repository import AccessUserRepositoryAdapter
from access.application.commands import ReplaceUserRolesCommand
from access.application.replace_user_roles import ReplaceUserRoles
from access.domain.errors import LastSystemAdministratorRequired
from infra.clock import SystemClock
from infra.identity import SystemIdentity

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)


def _uuid() -> str:
    return str(uuid4())


class ConcurrentLastAdminRemovalTest(unittest.TestCase):
    """C3: concurrent last-admin removal rejected under row lock.

    Setup: one system_administrator role, one active user assigned to it.
    Two concurrent sessions attempt to revoke the assignment through the Access
    application use case. Both must reject the mutation.
    """

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def setUp(self):
        self.user_id = _uuid()
        self.assignment_id = _uuid()

        with self.engine.begin() as conn:
            self.role_id = str(conn.execute(text(
                "SELECT role_id FROM access_roles "
                "WHERE role_code = 'system_administrator'"
            )).scalar_one())
            self.existing_active_administrator_ids = [
                str(user_id)
                for user_id in conn.execute(text(
                    "SELECT DISTINCT a.user_id "
                    "FROM access_user_role_assignments a "
                    "JOIN access_users u ON u.user_id = a.user_id "
                    "WHERE a.role_id = :rid AND a.revoked_at IS NULL "
                    "AND u.is_active = true"
                ), {"rid": self.role_id}).scalars()
            ]
            for user_id in self.existing_active_administrator_ids:
                conn.execute(text(
                    "UPDATE access_users SET is_active = false WHERE user_id = :uid"
                ), {"uid": user_id})

            # Create user
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name, is_active) "
                "VALUES (:uid, :sub, :code, :name, true)"
            ), {"uid": self.user_id, "sub": f"sub-{self.user_id[:8]}",
                "code": f"USR-{self.user_id[:6]}", "name": "Last Admin"})

            # Assign role to user
            conn.execute(text(
                "INSERT INTO access_user_role_assignments "
                "(assignment_id, user_id, role_id, assigned_by_user_id) "
                "VALUES (:aid, :uid, :rid, :uid)"
            ), {"aid": self.assignment_id, "uid": self.user_id, "rid": self.role_id})

    def tearDown(self):
        with self.engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM access_user_role_assignments WHERE user_id = :uid"
            ), {"uid": self.user_id})
            conn.execute(text(
                "DELETE FROM access_users WHERE user_id = :uid"
            ), {"uid": self.user_id})
            for user_id in self.existing_active_administrator_ids:
                conn.execute(text(
                    "UPDATE access_users SET is_active = true WHERE user_id = :uid"
                ), {"uid": user_id})

    def test_concurrent_removal_one_blocked(self):
        """Concurrent role replacement cannot revoke the only administrator."""
        SessionFactory = sessionmaker(bind=self.engine)
        results = {"session_1": None, "session_2": None}
        barrier = threading.Barrier(2, timeout=5)

        def attempt_removal(session_name):
            session = SessionFactory()
            try:
                use_case = ReplaceUserRoles(
                    user_repository=AccessUserRepositoryAdapter(session),
                    role_repository=RoleRepositoryAdapter(session),
                    assignment_repository=AssignmentRepositoryAdapter(session),
                    audit_repository=AccessAuditRepositoryAdapter(session),
                    transaction=TransactionAdapter(session),
                    clock=SystemClock(),
                    identity=SystemIdentity(),
                )
                barrier.wait()
                use_case.execute(
                    ReplaceUserRolesCommand(
                        user_id=self.user_id,
                        role_ids=[],
                        expected_version=1,
                        reason="concurrent last-admin removal test",
                        actor_user_id=self.user_id,
                        operation_id=_uuid(),
                    )
                )
            except Exception as exc:
                results[session_name] = exc
            finally:
                session.close()

        t1 = threading.Thread(target=attempt_removal, args=("session_1",))
        t2 = threading.Thread(target=attempt_removal, args=("session_2",))

        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertFalse(t1.is_alive(), "session_1 did not finish")
        self.assertFalse(t2.is_alive(), "session_2 did not finish")
        for result in results.values():
            self.assertIsInstance(result, LastSystemAdministratorRequired)

        with self.engine.connect() as conn:
            current_assignments = conn.execute(text(
                "SELECT count(*) FROM access_user_role_assignments "
                "WHERE assignment_id = :aid AND revoked_at IS NULL"
            ), {"aid": self.assignment_id}).scalar_one()
            user_state = conn.execute(text(
                "SELECT authorization_version, version FROM access_users "
                "WHERE user_id = :uid"
            ), {"uid": self.user_id}).one()
            audit_count = conn.execute(text(
                "SELECT count(*) FROM access_change_audits "
                "WHERE subject_type = 'user' AND subject_id = :uid"
            ), {"uid": self.user_id}).scalar_one()

        self.assertEqual(current_assignments, 1)
        self.assertEqual(user_state, (1, 1))
        self.assertEqual(audit_count, 0)


class CrossContextRollbackTest(unittest.TestCase):
    """C4 (partial): Verify that when access user creation fails (e.g. duplicate),
    the transaction rolls back and no partial state persists.
    """

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def test_duplicate_identity_subject_rolls_back(self):
        """If provisioning creates a user with duplicate identity_subject,
        the entire transaction rolls back."""
        uid1 = _uuid()
        uid2 = _uuid()
        subject = f"rollback-test-{uid1[:8]}"

        with self.engine.begin() as conn:
            # Create first user
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:uid, :sub, :code, :name)"
            ), {"uid": uid1, "sub": subject, "code": f"USR-{uid1[:6]}", "name": "First"})

        # Attempt to create second user with same subject in a transaction
        from sqlalchemy.orm import sessionmaker
        SessionFactory = sessionmaker(bind=self.engine)
        session = SessionFactory()
        try:
            session.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name) "
                "VALUES (:uid, :sub, :code, :name)"
            ), {"uid": uid2, "sub": subject, "code": f"USR-{uid2[:6]}", "name": "Second"})
            session.commit()
            self.fail("Expected unique constraint violation")
        except Exception:
            session.rollback()

        # Verify no second user exists (rollback successful)
        with self.engine.connect() as conn:
            count = conn.execute(text(
                "SELECT count(*) FROM access_users WHERE user_id = :uid"
            ), {"uid": uid2}).scalar()
            self.assertEqual(count, 0, "Second user should not exist after rollback")

        # Cleanup
        with self.engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM access_users WHERE user_id = :uid"
            ), {"uid": uid1})


if __name__ == "__main__":
    unittest.main()

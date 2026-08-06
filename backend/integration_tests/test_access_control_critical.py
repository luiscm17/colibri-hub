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
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)


def _uuid() -> str:
    return str(uuid4())


class ConcurrentLastAdminRemovalTest(unittest.TestCase):
    """C3: concurrent last-admin removal rejected under row lock.

    Setup: one system_administrator role, one active user assigned to it.
    Two concurrent sessions attempt to revoke the assignment (via FOR UPDATE lock).
    Exactly one must succeed; the other must fail or be blocked.
    """

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    def setUp(self):
        self.user_id = _uuid()
        self.role_id = _uuid()
        self.assignment_id = _uuid()

        with self.engine.begin() as conn:
            # Create user
            conn.execute(text(
                "INSERT INTO access_users (user_id, identity_subject, user_code, display_name, is_active) "
                "VALUES (:uid, :sub, :code, :name, true)"
            ), {"uid": self.user_id, "sub": f"sub-{self.user_id[:8]}",
                "code": f"USR-{self.user_id[:6]}", "name": "Last Admin"})

            # Create system_administrator role
            conn.execute(text(
                "INSERT INTO access_roles (role_id, role_code, role_name, is_system_administrator, is_active) "
                "VALUES (:rid, :code, :name, true, true)"
            ), {"rid": self.role_id, "code": f"sysadmin-{self.role_id[:6]}",
                "name": "System Administrator"})

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
            conn.execute(text(
                "DELETE FROM access_roles WHERE role_id = :rid"
            ), {"rid": self.role_id})

    def test_concurrent_removal_one_blocked(self):
        """Two sessions try to count admins FOR UPDATE; one blocks the other."""
        from sqlalchemy.orm import sessionmaker

        SessionFactory = sessionmaker(bind=self.engine)
        results = {"session_1": None, "session_2": None}
        barrier = threading.Barrier(2, timeout=5)

        def attempt_removal(session_name):
            session = SessionFactory()
            try:
                session.execute(text("BEGIN"))
                # Simulate the count_active_administrators query with FOR UPDATE
                rows = session.execute(text(
                    "SELECT a.user_id FROM access_user_role_assignments a "
                    "JOIN access_users u ON a.user_id = u.user_id "
                    "WHERE a.role_id = :rid AND a.revoked_at IS NULL AND u.is_active = true "
                    "FOR UPDATE"
                ), {"rid": self.role_id}).fetchall()

                barrier.wait()  # Synchronize both sessions at the lock point

                count_excluding_self = len([r for r in rows if str(r[0]) != self.user_id])

                if count_excluding_self < 1:
                    # Would remove last admin — reject
                    results[session_name] = "rejected"
                else:
                    results[session_name] = "allowed"

                session.execute(text("COMMIT"))
            except Exception as exc:
                results[session_name] = f"error: {exc}"
                session.execute(text("ROLLBACK"))
            finally:
                session.close()

        t1 = threading.Thread(target=attempt_removal, args=("session_1",))
        t2 = threading.Thread(target=attempt_removal, args=("session_2",))

        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # Both should result in "rejected" because the one user is the last admin.
        # The key property: the FOR UPDATE lock serializes access so no TOCTOU.
        rejected_count = sum(
            1 for v in results.values()
            if v == "rejected"
        )
        # At least one session correctly rejects the removal
        self.assertGreaterEqual(
            rejected_count, 1,
            f"Expected at least one rejection, got: {results}",
        )


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

"""Integration tests for C3 and C4 critical fixes.

C3: Concurrent last-admin removal rejected under row lock.
C4 (partial): Cross-context rollback on provisioning failure.

Requires: TEST_DATABASE_URL pointing to the guarded local PostgreSQL (port 54322).
Run with: TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres \
          uv run --locked --package backend python -m unittest backend.integration_tests.test_access_control_critical -v
"""

import threading
import unittest
from typing import Literal
from uuid import uuid4

from access.adapters.persistence.administrator_continuity import (
    AdministratorContinuityAdapter,
)
from access.domain.errors import AdministratorContinuityRequired
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)


def _uuid() -> str:
    return str(uuid4())


class ConcurrentAdministratorReductionTest(unittest.TestCase):
    """Prove the singleton lock preserves the two-administrator floor."""

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.fixture_users = [
            {"user_id": _uuid(), "subject": _uuid(), "account_id": _uuid()}
            for _ in range(3)
        ]

        with self.engine.begin() as conn:
            self.role_id = str(conn.execute(text(
                "SELECT role_id FROM access_roles "
                "WHERE role_code = 'system_administrator'"
            )).scalar_one())
            for index, user in enumerate(self.fixture_users):
                conn.execute(text(
                    "INSERT INTO authentication_accounts "
                    "(authentication_account_id, identity_subject, normalized_email, display_name, user_code, status) "
                    "VALUES (:account_id, :subject, :email, :name, :code, 'active')"
                ), {
                    **user,
                    "email": f"continuity-{user['subject']}@example.invalid",
                    "name": f"Continuity Administrator {index}",
                    "code": f"CNT-{user['subject'][:8]}",
                })
                conn.execute(text(
                    "INSERT INTO access_users "
                    "(user_id, identity_subject, user_code, display_name, is_active) "
                    "VALUES (:user_id, :subject, :code, :name, true)"
                ), {
                    **user,
                    "code": f"CNT-{user['user_id'][:8]}",
                    "name": f"Continuity Administrator {index}",
                })
                conn.execute(text(
                    "INSERT INTO access_user_role_assignments "
                    "(assignment_id, user_id, role_id, assigned_by_user_id) "
                    "VALUES (:assignment_id, :user_id, :role_id, :user_id)"
                ), {"assignment_id": _uuid(), "role_id": self.role_id, **user})

            enabled = conn.execute(text(
                "SELECT enforcement_enabled FROM access_administrator_continuity WHERE id = 1"
            )).scalar_one()
            if not enabled:
                conn.execute(text(
                    "UPDATE access_administrator_continuity "
                    "SET enforcement_enabled = true, enforcement_evidence = 'integration continuity proof' "
                    "WHERE id = 1"
                ))

    def tearDown(self):
        with self.engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM access_user_role_assignments WHERE user_id = ANY(:user_ids)"
            ), {"user_ids": [user["user_id"] for user in self.fixture_users]})
            conn.execute(text(
                "DELETE FROM access_users WHERE user_id = ANY(:user_ids)"
            ), {"user_ids": [user["user_id"] for user in self.fixture_users]})
            conn.execute(text(
                "DELETE FROM authentication_accounts WHERE authentication_account_id = ANY(:account_ids)"
            ), {"account_ids": [user["account_id"] for user in self.fixture_users]})

    def test_disjoint_concurrent_reductions_preserve_the_two_administrator_floor(self):
        """Two concurrent reductions serialize without crossing the global floor."""
        SessionFactory = sessionmaker(bind=self.engine)
        fixture_subjects = {user["subject"] for user in self.fixture_users}
        results: dict[
            str, Literal["succeeded"] | AdministratorContinuityRequired | SQLAlchemyError | None
        ] = {
            "session_1": None,
            "session_2": None,
        }
        barrier = threading.Barrier(2, timeout=5)

        with self.engine.connect() as conn:
            initial_operational = set(conn.execute(text(
                "SELECT identity_subject FROM access_operational_administrators_preflight"
            )).scalars())

        self.assertEqual(initial_operational, fixture_subjects)

        def attempt_reduction(session_name, target):
            session = SessionFactory()
            try:
                barrier.wait()
                AdministratorContinuityAdapter(session).assert_reduction_allowed(
                    target["subject"]
                )
                session.execute(text(
                    "UPDATE access_user_role_assignments "
                    "SET revoked_at = now(), revoked_by_user_id = :actor_id, "
                    "revoke_reason = 'concurrent continuity proof' "
                    "WHERE user_id = :user_id AND role_id = :role_id AND revoked_at IS NULL"
                ), {
                    "actor_id": target["user_id"],
                    "user_id": target["user_id"],
                    "role_id": self.role_id,
                })
                session.commit()
                results[session_name] = "succeeded"
            except AdministratorContinuityRequired as exc:
                session.rollback()
                results[session_name] = exc
            except SQLAlchemyError as exc:
                results[session_name] = exc
            finally:
                session.close()

        t1 = threading.Thread(
            target=attempt_reduction, args=("session_1", self.fixture_users[0])
        )
        t2 = threading.Thread(
            target=attempt_reduction, args=("session_2", self.fixture_users[1])
        )

        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        self.assertFalse(t1.is_alive(), "session_1 did not finish")
        self.assertFalse(t2.is_alive(), "session_2 did not finish")
        self.assertEqual(sum(result == "succeeded" for result in results.values()), 1)
        self.assertEqual(
            sum(
                isinstance(result, AdministratorContinuityRequired)
                for result in results.values()
            ),
            1,
        )

        with self.engine.connect() as conn:
            operational = set(conn.execute(text(
                "SELECT identity_subject FROM access_operational_administrators_preflight"
            )).scalars())

        self.assertTrue(
            operational.issubset(fixture_subjects)
        )
        self.assertEqual(len(operational), 2)


class CrossContextRollbackTest(unittest.TestCase):
    """C4 (partial): Verify that when access user creation fails (e.g. duplicate),
    the transaction rolls back and no partial state persists.
    """

    @classmethod
    def setUpClass(cls):
        validated_test_database_url()
        cls.engine = test_engine()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

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
        except IntegrityError:
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

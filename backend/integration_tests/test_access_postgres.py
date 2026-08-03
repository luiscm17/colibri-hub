import threading
import unittest
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from access.adapters.persistence.store import PostgresAccessStore
from access.application.services import AccessApplication, BootstrapConflict, FinalAdministratorRemoval, MutationCommand
from access.domain.models import SYSTEM_ADMINISTRATOR
from backend.integration_tests.database_test_support import test_engine


class AccessPostgreSQLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = test_engine()
        cls.tag = uuid4().hex
        session = Session(cls.engine)
        AccessApplication(PostgresAccessStore(session)).bootstrap(f"subject-{cls.tag}", f"PROFILE-{cls.tag}", f"bootstrap-{cls.tag}")
        session.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def app(self):
        session = Session(self.engine)
        return session, AccessApplication(PostgresAccessStore(session))

    def bootstrap(self):
        session, app = self.app(); tag = uuid4().hex
        app.bootstrap(f"subject-{tag}", f"PROFILE-{tag}", f"bootstrap-{tag}")
        return session, app, tag

    def test_bootstrap_retry_conflict_partial_state_and_two_canonical_scopes(self):
        session, app = self.app(); tag = self.tag
        self.assertTrue(app.bootstrap(f"subject-{tag}", f"PROFILE-{tag}", f"bootstrap-{tag}").global_access)
        with self.assertRaises(BootstrapConflict): app.bootstrap(f"subject-{tag}", "DIFFERENT", f"bootstrap-{tag}")
        self.assertEqual(session.execute(text("select array_agg(code order by code) from access_scopes")).scalar_one()[-2:], ["access_control", "warehouse.raw_materials"])
        session.close()
        partial = Session(self.engine); partial.execute(text("insert into access_scopes (code) values (:code)"), {"code": f"partial-{uuid4().hex}"}); partial.commit()
        with self.assertRaises(BootstrapConflict): AccessApplication(PostgresAccessStore(partial)).bootstrap("partial-subject", "PARTIAL", "partial-op")
        partial.close()

    def test_constraints_immutable_history_and_restricted_roles(self):
        session, app = self.app(); tag = self.tag
        with self.assertRaises(IntegrityError):
            session.execute(text("insert into access_profiles (subject, code) values (:subject, :code)"), {"subject": f"subject-{tag}", "code": f"DUP-{tag}"}); session.commit()
        session.rollback()
        with self.assertRaises(DBAPIError):
            session.execute(text("update access_profiles set subject = 'changed' where subject = :subject"), {"subject": f"subject-{tag}"}); session.commit()
        session.rollback()
        with self.assertRaises(DBAPIError):
            session.execute(text("delete from access_change_audit where operation_id = :operation"), {"operation": f"bootstrap-{tag}"}); session.commit()
        session.rollback(); session.close()
        with self.engine.connect() as connection:
            transaction = connection.begin()
            connection.execute(text("set local role anon"))
            with self.assertRaises(DBAPIError): connection.execute(text("select * from access_profiles"))
            transaction.rollback()

    def test_concurrent_final_administrator_removals_allow_only_one_commit(self):
        seed, app = self.app(); tag = self.tag
        other = f"other-{tag}"
        seed.execute(text("insert into access_profiles (subject, code) values (:subject, :code)"), {"subject": other, "code": f"OTHER-{tag}"}); seed.commit()
        app.create_current_assignment(MutationCommand(f"subject-{tag}", other, "add second administrator", f"assign-{tag}"), SYSTEM_ADMINISTRATOR)
        seed.close(); barrier = threading.Barrier(2); outcomes = []

        def remove(subject, operation):
            session, candidate = self.app(); barrier.wait()
            try:
                candidate.remove_current_assignment(MutationCommand(f"subject-{tag}", subject, "concurrent removal", operation), SYSTEM_ADMINISTRATOR); outcomes.append("committed")
            except FinalAdministratorRemoval: outcomes.append("rejected")
            finally: session.close()

        threads = [threading.Thread(target=remove, args=(f"subject-{tag}", f"remove-a-{tag}")), threading.Thread(target=remove, args=(other, f"remove-b-{tag}"))]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertCountEqual(outcomes, ["committed", "rejected"])

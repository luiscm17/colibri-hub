"""Guarded local-Supabase evidence for Authentication lifecycle use cases."""

import base64
import json
import subprocess
import unittest
from uuid import uuid4

from access.adapters.access_provisioning import AccessProvisioningAdapter
from access.adapters.persistence.administrator_continuity import (
    AdministratorContinuityAdapter,
)
from access.adapters.persistence.assignment_repository import (
    AssignmentRepositoryAdapter,
)
from access.adapters.persistence.audit_repository import AccessAuditRepositoryAdapter
from access.adapters.persistence.role_repository import RoleRepositoryAdapter
from access.adapters.persistence.transaction import TransactionAdapter
from access.adapters.persistence.user_repository import AccessUserRepositoryAdapter
from access.application.activate_access_user import ActivateAccessUser
from access.application.create_access_user import CreateAccessUser
from access.application.deactivate_access_user import DeactivateAccessUser
from access.domain.errors import AdministratorContinuityRequired
from auth.adapters.bootstrap_command import BootstrapInitialAdministrator
from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from auth.adapters.identity_provider.password_replacement import (
    SupabasePasswordReplacementAdapter,
)
from auth.adapters.persistence.account_repository import AuthAccountRepositoryAdapter
from auth.adapters.persistence.audit_repository import AuthAuditRepositoryAdapter
from auth.application.change_required_password import ChangeRequiredPassword
from auth.application.commands import (
    ChangePasswordCommand,
    DisableAccountCommand,
    ProvisionAccountCommand,
    ResetPasswordCommand,
)
from auth.application.disable_account import DisableAccount
from auth.application.get_current_authentication import GetCurrentAuthentication
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.errors import CurrentPasswordRejected
from infra.clock import SystemClock
from infra.identity import SystemIdentity
from sqlalchemy import text
from sqlalchemy.orm import Session
from supabase_auth.errors import AuthError

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)
from supabase import create_client


class AuthLifecycleLocalSupabaseIntegrationTests(unittest.TestCase):
    """Exercise real use-case composition without HTTP/JWT orchestration."""

    @classmethod
    def setUpClass(cls) -> None:
        validated_test_database_url()
        cls.engine = test_engine()
        cls.provider_url, cls.service_role_key = cls._local_provider_credentials()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self._clients = []
        self._deactivate_owned_lifecycle_fixtures()

    def tearDown(self) -> None:
        for client in self._clients:
            client.auth.close()

    def test_record_logout_revokes_only_the_passed_provider_session(self) -> None:
        fixture = self._active_target_fixture()
        try:
            session_a = self._sign_in(fixture.email, fixture.password)
            session_b = self._sign_in(fixture.email, fixture.password)
            self.assertNotEqual(session_a, session_b)

            fixture.use_cases.record_logout.execute(
                identity_subject=fixture.subject, session_id=session_a
            )
            fixture.session.commit()

            self.assertFalse(self._has_session(session_a, fixture.subject))
            self.assertTrue(self._has_session(session_b, fixture.subject))
        finally:
            fixture.close()

    def test_reset_password_revokes_target_sessions_and_keeps_access_active(
        self,
    ) -> None:
        fixture = self._active_target_fixture()
        support_fixtures = [self._active_target_fixture() for _ in range(2)]
        try:
            session_a = self._sign_in(fixture.email, fixture.password)
            session_b = self._sign_in(fixture.email, fixture.password)

            fixture.use_cases.reset_password.execute(
                ResetPasswordCommand(
                    account_id=fixture.account_id,
                    provisional_password="ReplacementPass1!",
                    reason="integration evidence",
                    expected_version=2,
                    actor_subject=fixture.admin_subject,
                )
            )
            fixture.session.commit()

            account = AuthAccountRepositoryAdapter(fixture.session).find_by_id(
                fixture.account_id
            )
            assert account is not None
            self.assertEqual(
                account.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
            )
            self.assertFalse(self._has_session(session_a, fixture.subject))
            self.assertFalse(self._has_session(session_b, fixture.subject))
            profile = AccessUserRepositoryAdapter(fixture.session).find_by_subject(
                fixture.subject
            )
            assert profile is not None
            self.assertTrue(profile.is_active)
        finally:
            for support_fixture in support_fixtures:
                support_fixture.close()
            fixture.close()

    def test_disable_account_revokes_sessions_and_deactivates_access_profile(
        self,
    ) -> None:
        fixture = self._active_target_fixture()
        support_fixtures = [self._active_target_fixture() for _ in range(2)]
        try:
            session_a = self._sign_in(fixture.email, fixture.password)
            session_b = self._sign_in(fixture.email, fixture.password)

            fixture.use_cases.disable_account.execute(
                DisableAccountCommand(
                    account_id=fixture.account_id,
                    reason="integration evidence",
                    expected_version=2,
                    actor_subject=fixture.admin_subject,
                )
            )
            fixture.session.commit()

            account = AuthAccountRepositoryAdapter(fixture.session).find_by_id(
                fixture.account_id
            )
            assert account is not None
            self.assertEqual(account.status, AuthenticationAccountStatus.DISABLED)
            self.assertFalse(self._has_session(session_a, fixture.subject))
            self.assertFalse(self._has_session(session_b, fixture.subject))
            profile = AccessUserRepositoryAdapter(fixture.session).find_by_subject(
                fixture.subject
            )
            assert profile is not None
            self.assertFalse(profile.is_active)
        finally:
            for support_fixture in support_fixtures:
                support_fixture.close()
            fixture.close()

    def test_z_continuity_allows_three_to_two_then_rejects_two_to_one_before_provider_calls(
        self,
    ) -> None:
        """Use owned operational administrators to prove lifecycle continuity."""
        fixtures = self._operational_administrator_fixtures(3)
        try:
            fixture_subjects = {fixture.subject for fixture in fixtures}
            self.assertEqual(
                self._operational_administrator_subjects(), fixture_subjects
            )
            reducing_fixture = fixtures[0]
            reducing_fixture.use_cases.disable_account.execute(
                DisableAccountCommand(
                    account_id=reducing_fixture.account_id,
                    reason="integration continuity proof",
                    expected_version=2,
                    actor_subject=fixtures[1].subject,
                )
            )

            reduced_account = AuthAccountRepositoryAdapter(
                reducing_fixture.session
            ).find_by_id(reducing_fixture.account_id)
            reduced_profile = AccessUserRepositoryAdapter(
                reducing_fixture.session
            ).find_by_subject(reducing_fixture.subject)
            assert reduced_account is not None
            assert reduced_profile is not None
            self.assertEqual(
                reduced_account.status, AuthenticationAccountStatus.DISABLED
            )
            self.assertFalse(reduced_profile.is_active)
            self.assertEqual(
                self._operational_administrator_subjects(),
                {fixture.subject for fixture in fixtures[1:]},
            )

            rejected_fixture = fixtures[1]
            rejected_session = self._sign_in(
                rejected_fixture.email, rejected_fixture.password
            )
            with self.assertRaises(AdministratorContinuityRequired):
                rejected_fixture.use_cases.disable_account.execute(
                    DisableAccountCommand(
                        account_id=rejected_fixture.account_id,
                        reason="must preserve the floor",
                        expected_version=2,
                        actor_subject=fixtures[2].subject,
                    )
                )
            rejected_fixture.session.rollback()

            rejected_account = AuthAccountRepositoryAdapter(
                rejected_fixture.session
            ).find_by_id(rejected_fixture.account_id)
            rejected_profile = AccessUserRepositoryAdapter(
                rejected_fixture.session
            ).find_by_subject(rejected_fixture.subject)
            assert rejected_account is not None
            assert rejected_profile is not None
            self.assertEqual(
                rejected_account.status, AuthenticationAccountStatus.ACTIVE
            )
            self.assertTrue(rejected_profile.is_active)
            self.assertTrue(
                self._has_session(rejected_session, rejected_fixture.subject)
            )
        finally:
            for fixture in fixtures:
                fixture.close()

    def test_required_password_replacement_requires_fresh_login_before_access(
        self,
    ) -> None:
        fixture = self._awaiting_target_fixture()
        try:
            original_login = self._sign_in_response(fixture.email, fixture.password)
            assert original_login.session is not None
            original_session_id = self._session_id(original_login.session.access_token)

            with self.assertRaises(CurrentPasswordRejected):
                fixture.use_cases.change_required_password.execute(
                    ChangePasswordCommand(
                        current_password="wrong-current-password",
                        new_password="SyntheticLifecycleReplacement2!",
                        actor_subject=fixture.subject,
                        session_id=original_session_id,
                    )
                )

            awaiting = AuthAccountRepositoryAdapter(fixture.session).find_by_id(
                fixture.account_id
            )
            assert awaiting is not None
            self.assertEqual(
                awaiting.status, AuthenticationAccountStatus.AWAITING_PASSWORD_CHANGE
            )
            self.assertTrue(self._can_sign_in(fixture.email, fixture.password))

            replacement_password = "SyntheticLifecycleReplacement2!"
            fixture.use_cases.change_required_password.execute(
                ChangePasswordCommand(
                    current_password=fixture.password,
                    new_password=replacement_password,
                    actor_subject=fixture.subject,
                    session_id=original_session_id,
                )
            )
            fixture.session.commit()

            active = AuthAccountRepositoryAdapter(fixture.session).find_by_id(
                fixture.account_id
            )
            assert active is not None
            self.assertEqual(active.status, AuthenticationAccountStatus.ACTIVE)
            self.assertFalse(self._can_sign_in(fixture.email, fixture.password))
            self.assertTrue(
                self._prior_bearer_is_rejected(original_login.session.access_token)
            )

            fresh_login = self._sign_in_response(fixture.email, replacement_password)
            self.assertIsNotNone(fresh_login.session)
            self.assertIsNotNone(fresh_login.user)
            assert fresh_login.user is not None
            self.assertEqual(str(fresh_login.user.id), fixture.subject)
            self.assertEqual(
                fixture.use_cases.get_current_authentication.execute(
                    fixture.subject
                ).next_step,
                "load_access",
            )
        finally:
            fixture.close()

    def _active_target_fixture(self):
        fixture = self._awaiting_target_fixture()
        try:
            activation_session = self._sign_in(fixture.email, fixture.password)
            fixture.use_cases.change_required_password.execute(
                ChangePasswordCommand(
                    current_password=fixture.password,
                    new_password=fixture.password + "Changed",
                    actor_subject=fixture.subject,
                    session_id=activation_session,
                )
            )
            fixture.session.commit()
            fixture.password += "Changed"
            return fixture
        except Exception:
            fixture.close()
            raise

    def _operational_administrator_fixtures(
        self,
        count: int,
    ) -> list["_LifecycleFixture"]:
        """Create only test-owned active administrators before enabling the guard."""
        fixtures = []
        try:
            for _ in range(count):
                fixtures.append(self._active_target_fixture())
            with self.engine.begin() as connection:
                enabled = connection.execute(
                    text(
                        "SELECT enforcement_enabled "
                        "FROM access_administrator_continuity WHERE id = 1"
                    )
                ).scalar_one()
                if not enabled:
                    connection.execute(
                        text(
                            "UPDATE access_administrator_continuity "
                            "SET enforcement_enabled = true, "
                            "enforcement_evidence = 'lifecycle integration continuity proof' "
                            "WHERE id = 1"
                        )
                    )
            return fixtures
        except Exception:
            for fixture in fixtures:
                fixture.close()
            raise

    def _awaiting_target_fixture(self):
        session = Session(self.engine)
        use_cases = self._use_cases(session)
        token = uuid4().hex
        password = "SyntheticLifecyclePass1!"
        admin_email = f"lifecycle-admin-{token}@example.invalid"
        target_email = f"lifecycle-target-{token}@example.invalid"
        admin_code = f"ADM-{token[:8]}"
        target_code = f"USR-{token[:8]}"
        subjects: list[str] = []
        try:
            bootstrap = BootstrapInitialAdministrator(
                account_repository=AuthAccountRepositoryAdapter(session),
                audit_repository=AuthAuditRepositoryAdapter(session),
                identity_provider=IdentityProviderAdapter(self._client(), session),
                access_provisioning=self._access_provisioning(session),
                clock=SystemClock(),
                identity=SystemIdentity(),
            )
            admin_account_id = bootstrap.execute(
                email=admin_email,
                provisional_password=password,
                user_code=admin_code,
                display_name="Lifecycle Administrator",
            )
            session.commit()
            admin = AuthAccountRepositoryAdapter(session).find_by_id(admin_account_id)
            assert admin is not None
            subjects.append(admin.identity_subject)

            target = use_cases.provision_account.execute(
                ProvisionAccountCommand(
                    email=target_email,
                    provisional_password=password,
                    user_code=target_code,
                    display_name="Lifecycle Target",
                    role_codes=["system_administrator"],
                    reason="integration fixture",
                    actor_subject=admin.identity_subject,
                )
            )
            session.commit()
            account = AuthAccountRepositoryAdapter(session).find_by_id(
                target.account_id
            )
            assert account is not None
            subjects.append(account.identity_subject)
            return _LifecycleFixture(
                session,
                use_cases,
                target.account_id,
                account.identity_subject,
                admin.identity_subject,
                target_email,
                password,
                subjects,
                self,
            )
        except Exception:
            session.rollback()
            for subject in subjects:
                IdentityProviderAdapter(self._client(), session).delete_user(
                    subject=subject
                )
            use_cases.password_replacement.close()
            session.close()
            raise

    def _use_cases(self, session: Session) -> "_LifecycleUseCases":
        accounts = AuthAccountRepositoryAdapter(session)
        audits = AuthAuditRepositoryAdapter(session)
        provider = IdentityProviderAdapter(self._client(), session)
        clock = SystemClock()
        identity = SystemIdentity()
        access = self._access_provisioning(session)
        transaction = TransactionAdapter(session)
        password_replacement = SupabasePasswordReplacementAdapter(
            provider_url=self.provider_url,
            service_role_key=self.service_role_key,
            database_session=session,
        )
        return _LifecycleUseCases(
            get_current_authentication=GetCurrentAuthentication(accounts),
            change_required_password=ChangeRequiredPassword(
                account_repository=accounts,
                audit_repository=audits,
                password_replacement=password_replacement,
                clock=clock,
                identity=identity,
            ),
            record_logout=RecordLogout(
                account_repository=accounts,
                audit_repository=audits,
                identity_provider=provider,
                clock=clock,
                identity=identity,
            ),
            provision_account=ProvisionAccount(
                account_repository=accounts,
                audit_repository=audits,
                identity_provider=provider,
                access_provisioning=access,
                clock=clock,
                identity=identity,
            ),
            reset_password=ResetPassword(
                account_repository=accounts,
                audit_repository=audits,
                identity_provider=provider,
                access_provisioning=access,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            password_replacement=password_replacement,
            disable_account=DisableAccount(
                account_repository=accounts,
                audit_repository=audits,
                identity_provider=provider,
                access_provisioning=access,
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
        )

    def _access_provisioning(self, session: Session) -> AccessProvisioningAdapter:
        users = AccessUserRepositoryAdapter(session)
        transaction = TransactionAdapter(session)
        continuity = AdministratorContinuityAdapter(session)
        clock = SystemClock()
        identity = SystemIdentity()
        return AccessProvisioningAdapter(
            create_user=CreateAccessUser(
                user_repository=users,
                role_repository=RoleRepositoryAdapter(session),
                assignment_repository=AssignmentRepositoryAdapter(session),
                audit_repository=AccessAuditRepositoryAdapter(session),
                transaction=transaction,
                clock=clock,
                identity=identity,
            ),
            activate_user=ActivateAccessUser(
                user_repository=users,
                audit_repository=AccessAuditRepositoryAdapter(session),
                transaction=transaction,
                clock=clock,
            ),
            deactivate_user=DeactivateAccessUser(
                user_repository=users,
                audit_repository=AccessAuditRepositoryAdapter(session),
                transaction=transaction,
                clock=clock,
                continuity=continuity,
            ),
            continuity=continuity,
        )

    def _client(self):
        client = create_client(self.provider_url, self.service_role_key)
        self._clients.append(client)
        return client

    def _sign_in(self, email: str, password: str) -> str:
        response = self._sign_in_response(email, password)
        assert response.session is not None
        return self._session_id(response.session.access_token)

    def _sign_in_response(self, email: str, password: str):
        return self._client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )

    @staticmethod
    def _session_id(access_token: str) -> str:
        payload = access_token.split(".")[1]
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        return json.loads(decoded)["session_id"]

    def _can_sign_in(self, email: str, password: str) -> bool:
        try:
            response = self._sign_in_response(email, password)
        except AuthError:
            return False
        return response.session is not None

    def _prior_bearer_is_rejected(self, bearer: str) -> bool:
        try:
            self._client().auth.get_user(bearer)
        except AuthError:
            return True
        return False

    def _has_session(self, session_id: str, subject: str) -> bool:
        verification = Session(self.engine)
        try:
            return IdentityProviderAdapter(
                self._client(), verification
            ).has_active_session(session_id=session_id, subject=subject)
        finally:
            verification.rollback()
            verification.close()

    def _operational_administrator_subjects(self) -> set[str]:
        with self.engine.connect() as connection:
            return set(
                connection.execute(
                    text(
                        "SELECT identity_subject "
                        "FROM access_operational_administrators_preflight"
                    )
                ).scalars()
            )

    def _deactivate_owned_lifecycle_fixtures(self) -> None:
        """Keep retained audit evidence from prior runs out of the continuity count."""
        with self.engine.begin() as connection:
            subjects = [
                str(subject)
                for subject in connection.execute(
                    text(
                        "SELECT identity_subject FROM authentication_accounts "
                        "WHERE normalized_email LIKE 'lifecycle-%@example.invalid' "
                        "AND status = 'active'"
                    )
                ).scalars()
            ]
            connection.execute(
                text(
                    "UPDATE authentication_accounts SET status = 'disabled' "
                    "WHERE normalized_email LIKE 'lifecycle-%@example.invalid' "
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


class _LifecycleFixture:
    def __init__(
        self,
        session,
        use_cases,
        account_id,
        subject,
        admin_subject,
        email,
        password,
        subjects,
        test,
    ):
        self.session, self.use_cases, self.account_id = session, use_cases, account_id
        self.subject, self.admin_subject, self.email, self.password = (
            subject,
            admin_subject,
            email,
            password,
        )
        self._subjects, self._test = subjects, test

    def close(self) -> None:
        self.session.rollback()
        for subject in self._subjects:
            IdentityProviderAdapter(self._test._client(), self.session).delete_user(
                subject=subject
            )
        self.session.execute(
            text(
                "UPDATE authentication_accounts SET status = 'disabled' "
                "WHERE identity_subject::text = ANY(:subjects) AND status = 'active'"
            ),
            {"subjects": self._subjects},
        )
        self.session.execute(
            text(
                "UPDATE access_users SET is_active = false "
                "WHERE identity_subject = ANY(:subjects)"
            ),
            {"subjects": self._subjects},
        )
        self.session.commit()
        self.use_cases.password_replacement.close()
        self.session.close()


class _LifecycleUseCases:
    def __init__(
        self,
        *,
        get_current_authentication: GetCurrentAuthentication,
        change_required_password: ChangeRequiredPassword,
        record_logout: RecordLogout,
        provision_account: ProvisionAccount,
        reset_password: ResetPassword,
        disable_account: DisableAccount,
        password_replacement: SupabasePasswordReplacementAdapter,
    ) -> None:
        self.get_current_authentication = get_current_authentication
        self.change_required_password = change_required_password
        self.record_logout = record_logout
        self.provision_account = provision_account
        self.reset_password = reset_password
        self.disable_account = disable_account
        self.password_replacement = password_replacement


if __name__ == "__main__":
    unittest.main()

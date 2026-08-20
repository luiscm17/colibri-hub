"""Guarded local-Supabase evidence for Authentication lifecycle use cases."""

import base64
import json
import subprocess
import unittest
from uuid import uuid4

from access.adapters.access_provisioning import AccessProvisioningAdapter
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
from auth.adapters.bootstrap_command import BootstrapInitialAdministrator
from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
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
from auth.application.provision_account import ProvisionAccount
from auth.application.record_logout import RecordLogout
from auth.application.reset_password import ResetPassword
from auth.domain.account_status import AuthenticationAccountStatus
from infra.clock import SystemClock
from infra.identity import SystemIdentity
from sqlalchemy.orm import Session

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

    def test_reset_password_revokes_target_sessions_and_keeps_access_active(self) -> None:
        fixture = self._active_target_fixture()
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
            fixture.close()

    def test_disable_account_revokes_sessions_and_deactivates_access_profile(self) -> None:
        fixture = self._active_target_fixture()
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
            fixture.close()

    def _active_target_fixture(self):
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
            account = AuthAccountRepositoryAdapter(session).find_by_id(target.account_id)
            assert account is not None
            subjects.append(account.identity_subject)
            activation_session = self._sign_in(target_email, password)
            use_cases.change_required_password.execute(
                ChangePasswordCommand(
                    current_password=password,
                    new_password=password + "Changed",
                    actor_subject=account.identity_subject,
                    session_id=activation_session,
                )
            )
            session.commit()
            return _LifecycleFixture(
                session, use_cases, target.account_id, account.identity_subject,
                admin.identity_subject, target_email, password + "Changed", subjects, self
            )
        except Exception:
            session.rollback()
            for subject in subjects:
                IdentityProviderAdapter(self._client(), session).delete_user(subject=subject)
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
        return _LifecycleUseCases(
            change_required_password=ChangeRequiredPassword(account_repository=accounts, audit_repository=audits, identity_provider=provider, clock=clock, identity=identity),
            record_logout=RecordLogout(account_repository=accounts, audit_repository=audits, identity_provider=provider, clock=clock, identity=identity),
            provision_account=ProvisionAccount(account_repository=accounts, audit_repository=audits, identity_provider=provider, access_provisioning=access, clock=clock, identity=identity),
            reset_password=ResetPassword(account_repository=accounts, audit_repository=audits, identity_provider=provider, access_provisioning=access, transaction=transaction, clock=clock, identity=identity),
            disable_account=DisableAccount(account_repository=accounts, audit_repository=audits, identity_provider=provider, access_provisioning=access, transaction=transaction, clock=clock, identity=identity),
        )

    def _access_provisioning(self, session: Session) -> AccessProvisioningAdapter:
        users = AccessUserRepositoryAdapter(session)
        transaction = TransactionAdapter(session)
        clock = SystemClock()
        identity = SystemIdentity()
        return AccessProvisioningAdapter(
            create_user=CreateAccessUser(user_repository=users, role_repository=RoleRepositoryAdapter(session), assignment_repository=AssignmentRepositoryAdapter(session), audit_repository=AccessAuditRepositoryAdapter(session), transaction=transaction, clock=clock, identity=identity),
            activate_user=ActivateAccessUser(user_repository=users, audit_repository=AccessAuditRepositoryAdapter(session), transaction=transaction, clock=clock),
            deactivate_user=DeactivateAccessUser(user_repository=users, audit_repository=AccessAuditRepositoryAdapter(session), transaction=transaction, clock=clock),
            user_repository=users,
        )

    def _client(self):
        return create_client(self.provider_url, self.service_role_key)

    def _sign_in(self, email: str, password: str) -> str:
        response = self._client().auth.sign_in_with_password({"email": email, "password": password})
        assert response.session is not None
        payload = response.session.access_token.split(".")[1]
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        return json.loads(decoded)["session_id"]

    def _has_session(self, session_id: str, subject: str) -> bool:
        verification = Session(self.engine)
        try:
            return IdentityProviderAdapter(self._client(), verification).has_active_session(session_id=session_id, subject=subject)
        finally:
            verification.rollback()
            verification.close()

    @staticmethod
    def _local_provider_credentials() -> tuple[str, str]:
        result = subprocess.run(["pnpm", "supabase", "status", "--output", "env"], capture_output=True, text=True, check=True)
        values = {}
        for line in result.stdout.splitlines():
            key, separator, value = line.removeprefix("export ").partition("=")
            if separator:
                values[key] = value.strip("'\"")
        return values["API_URL"], values["SERVICE_ROLE_KEY"]


class _LifecycleFixture:
    def __init__(self, session, use_cases, account_id, subject, admin_subject, email, password, subjects, test):
        self.session, self.use_cases, self.account_id = session, use_cases, account_id
        self.subject, self.admin_subject, self.email, self.password = subject, admin_subject, email, password
        self._subjects, self._test = subjects, test

    def close(self) -> None:
        self.session.rollback()
        for subject in self._subjects:
            IdentityProviderAdapter(self._test._client(), self.session).delete_user(subject=subject)
        self.session.close()


class _LifecycleUseCases:
    def __init__(
        self,
        *,
        change_required_password: ChangeRequiredPassword,
        record_logout: RecordLogout,
        provision_account: ProvisionAccount,
        reset_password: ResetPassword,
        disable_account: DisableAccount,
    ) -> None:
        self.change_required_password = change_required_password
        self.record_logout = record_logout
        self.provision_account = provision_account
        self.reset_password = reset_password
        self.disable_account = disable_account


if __name__ == "__main__":
    unittest.main()

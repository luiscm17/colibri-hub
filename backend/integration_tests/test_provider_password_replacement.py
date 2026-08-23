"""Controlled, credential-safe local capability gate for password replacement.

This harness intentionally proves no production capability. The locally
controlled Supabase Auth configuration is eligible only when every assertion
passes. It records booleans and safe classifications only; credentials, tokens,
session identifiers, and provider payloads remain in process and are never
emitted.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from infra.configuration import ApplicationSettings
from sqlalchemy.orm import Session
from supabase_auth.errors import AuthError

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)
from supabase import create_client


@dataclass(frozen=True, slots=True)
class _ProviderConfiguration:
    label: str
    url: str | None
    service_role_key: str | None

    @property
    def available(self) -> bool:
        return bool(self.url and self.service_role_key)


@dataclass(slots=True)
class _GateEvidence:
    configuration: str
    configuration_available: bool
    wrong_current_rejected: bool = False
    wrong_current_no_side_effect: bool = False
    old_login_rejected: bool = False
    new_login_succeeds: bool = False
    correct_current_replacement: bool = False
    previous_provider_session_terminated: bool = False
    fresh_login_access_eligible: bool = False
    disposable_identity_cleanup_succeeded: bool = False
    provider_failure_classification: str = "not_run"

    @property
    def eligible(self) -> bool:
        return (
            self.configuration_available
            and self.wrong_current_rejected
            and self.wrong_current_no_side_effect
            and self.correct_current_replacement
            and self.old_login_rejected
            and self.new_login_succeeds
            and self.previous_provider_session_terminated
            and self.fresh_login_access_eligible
            and self.disposable_identity_cleanup_succeeded
            and self.provider_failure_classification == "none"
        )

    def safe_summary(self) -> str:
        return (
            f"configuration={self.configuration} "
            f"available={self.configuration_available} "
            f"wrong_current_rejected={self.wrong_current_rejected} "
            f"wrong_current_no_side_effect={self.wrong_current_no_side_effect} "
            f"correct_current_replacement={self.correct_current_replacement} "
            f"old_login_rejected={self.old_login_rejected} "
            f"new_login_succeeds={self.new_login_succeeds} "
            "previous_provider_session_terminated="
            f"{self.previous_provider_session_terminated} "
            f"fresh_login_access_eligible={self.fresh_login_access_eligible} "
            "disposable_identity_cleanup_succeeded="
            f"{self.disposable_identity_cleanup_succeeded} "
            f"provider_failure_classification={self.provider_failure_classification}"
        )


class ProviderPasswordReplacementCapabilityGateTests(unittest.TestCase):
    """Evaluate the local provider sequence without selecting a production adapter."""

    @classmethod
    def setUpClass(cls) -> None:
        validated_test_database_url()
        cls.engine = test_engine()

    def test_requires_passing_local_evidence(self) -> None:
        evidence = [self._run_gate(configuration) for configuration in self._configs()]

        for result in evidence:
            print(f"PASSWORD_REPLACEMENT_CAPABILITY_GATE {result.safe_summary()}")
        self.assertTrue(
            all(result.eligible for result in evidence),
            "; ".join(result.safe_summary() for result in evidence),
        )

    def _configs(self) -> tuple[_ProviderConfiguration, ...]:
        settings = ApplicationSettings.from_environment(Path("backend/.env"))
        local = settings.auth_provider
        return (
            _ProviderConfiguration(
                label="local",
                url=local.url if local is not None else None,
                service_role_key=(
                    local.service_role_key.get_secret_value() if local is not None else None
                ),
            ),
        )

    def _run_gate(self, configuration: _ProviderConfiguration) -> _GateEvidence:
        evidence = _GateEvidence(
            configuration=configuration.label,
            configuration_available=configuration.available,
        )
        if not configuration.available:
            evidence.provider_failure_classification = "unavailable"
            return evidence

        assert configuration.url is not None
        assert configuration.service_role_key is not None
        email = f"password-replacement-gate-{uuid4().hex}@example.invalid"
        current_password = "ControlledCurrentPass1!"
        wrong_current_password = "ControlledWrongPass2!"
        replacement_password = "ControlledReplacementPass3!"
        subject: str | None = None
        database_session = Session(self.engine)

        try:
            admin_client = create_client(
                configuration.url, configuration.service_role_key
            )
            identity = IdentityProviderAdapter(admin_client, database_session).create_user(
                email=email,
                password=current_password,
            )
            subject = identity.subject
            original_session_client = create_client(
                configuration.url, configuration.service_role_key
            )
            sign_in = original_session_client.auth.sign_in_with_password(
                {"email": email, "password": current_password}
            )
            original_session = sign_in.session
            if original_session is None:
                evidence.provider_failure_classification = "unavailable"
                return evidence

            wrong_attempt = self._verify_current_password(
                configuration,
                email=email,
                current_password=wrong_current_password,
                expected_subject=subject,
            )
            evidence.wrong_current_rejected = wrong_attempt == "rejected"
            if not evidence.wrong_current_rejected:
                evidence.provider_failure_classification = wrong_attempt
                return evidence

            evidence.wrong_current_no_side_effect = self._can_sign_in(
                configuration, email, current_password
            ) and not self._can_sign_in(
                configuration, email, replacement_password
            ) and self._bearer_is_usable(
                configuration, original_session.access_token
            )
            if not evidence.wrong_current_no_side_effect:
                evidence.provider_failure_classification = "side_effect"
                return evidence

            correct_attempt = self._verify_current_password(
                configuration,
                email=email,
                current_password=current_password,
                expected_subject=subject,
            )
            if correct_attempt != "accepted":
                evidence.provider_failure_classification = correct_attempt
                return evidence

            replacement_attempt = self._replace_password_with_verified_current(
                original_session_client,
                current_password=current_password,
                new_password=replacement_password,
            )
            if replacement_attempt != "accepted":
                evidence.provider_failure_classification = replacement_attempt
                return evidence
            evidence.correct_current_replacement = True

            evidence.old_login_rejected = not self._can_sign_in(
                configuration, email, current_password
            )
            evidence.previous_provider_session_terminated = self._terminate_session(
                original_session_client,
                configuration=configuration,
                bearer=original_session.access_token,
            )
            fresh_login = self._sign_in(
                configuration, email, replacement_password
            )
            evidence.new_login_succeeds = fresh_login is not None
            evidence.fresh_login_access_eligible = (
                fresh_login is not None
                and fresh_login.user is not None
                and str(fresh_login.user.id) == subject
            )
            evidence.provider_failure_classification = "none"
            return evidence
        except Exception:  # noqa: BLE001 - provider failures must stay credential-safe.
            evidence.provider_failure_classification = "unavailable"
            return evidence
        finally:
            database_session.rollback()
            database_session.close()
            if subject is not None:
                evidence.disposable_identity_cleanup_succeeded = (
                    self._delete_disposable_identity(configuration, subject)
                )

    @staticmethod
    def _verify_current_password(
        configuration: _ProviderConfiguration,
        *,
        email: str,
        current_password: str,
        expected_subject: str,
    ) -> str:
        """Verify only through a separate disposable client; never hand off its session."""
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            verification_client = create_client(
                configuration.url, configuration.service_role_key
            )
            response = verification_client.auth.sign_in_with_password(
                {"email": email, "password": current_password}
            )
        except AuthError:
            return "rejected"
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return "unavailable"
        if response.session is None or response.user is None:
            return "unavailable"
        if str(response.user.id) != expected_subject:
            return "unavailable"
        return "accepted"

    @staticmethod
    def _replace_password_with_verified_current(
        client, *, current_password: str, new_password: str
    ) -> str:
        """Require the provider's native current-password verification on mutation."""
        try:
            client.auth.update_user(
                {"password": new_password, "current_password": current_password}
            )
        except AuthError:
            return "rejected"
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return "unavailable"
        return "accepted"

    @staticmethod
    def _terminate_session(client, *, configuration: _ProviderConfiguration, bearer: str) -> bool:
        """Terminate the replacement session and prove its prior bearer is rejected."""
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            client.auth.sign_out()
            create_client(
                configuration.url, configuration.service_role_key
            ).auth.get_user(bearer)
        except AuthError:
            return True
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return False
        return False

    @staticmethod
    def _bearer_is_usable(configuration: _ProviderConfiguration, bearer: str) -> bool:
        """Check a bearer only in process; never emit its value or decoded claims."""
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            response = create_client(
                configuration.url, configuration.service_role_key
            ).auth.get_user(bearer)
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return False
        return response is not None and response.user is not None

    @staticmethod
    def _sign_in(configuration: _ProviderConfiguration, email: str, password: str):
        """Return a fresh provider-authenticated session without emitting its contents."""
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            return create_client(
                configuration.url, configuration.service_role_key
            ).auth.sign_in_with_password({"email": email, "password": password})
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return None

    @staticmethod
    def _can_sign_in(
        configuration: _ProviderConfiguration, email: str, password: str
    ) -> bool:
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            response = ProviderPasswordReplacementCapabilityGateTests._sign_in(
                configuration, email, password
            )
        except Exception:  # noqa: BLE001 - never surface a raw provider failure.
            return False
        return response is not None and response.session is not None

    def _delete_disposable_identity(
        self, configuration: _ProviderConfiguration, subject: str
    ) -> bool:
        assert configuration.url is not None
        assert configuration.service_role_key is not None
        try:
            cleanup_session = Session(self.engine)
            try:
                IdentityProviderAdapter(
                    create_client(configuration.url, configuration.service_role_key),
                    cleanup_session,
                ).delete_user(subject=subject)
                return True
            finally:
                cleanup_session.rollback()
                cleanup_session.close()
        except Exception:  # noqa: BLE001 - cleanup cannot expose provider data.
            # Cleanup is best effort and never emits provider details.
            return False


if __name__ == "__main__":
    unittest.main()

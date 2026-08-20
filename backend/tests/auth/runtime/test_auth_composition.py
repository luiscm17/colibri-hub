import unittest
from datetime import UTC, datetime
from typing import Annotated
from unittest.mock import MagicMock, patch

from auth.domain.account import AuthenticationAccount
from auth.domain.account_status import AuthenticationAccountStatus
from auth.domain.email import NormalizedEmail
from bootstrap.auth_dependency import compose_auth
from bootstrap.database_session_dependency import session_dependency
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from infra.configuration import (
    ApplicationSettings,
    AuthProviderSettings,
    DatabaseSettings,
)
from pydantic import SecretStr
from shared.identity import AuthenticatedIdentity


def _settings() -> ApplicationSettings:
    return ApplicationSettings(
        database=DatabaseSettings(url=SecretStr("sqlite+pysqlite:///:memory:")),
        auth_provider=AuthProviderSettings(
            url="http://provider.test",
            service_role_key=SecretStr("service-role-key"),
            jwt_secret=SecretStr("jwt-secret"),
        ),
    )


def _active_account() -> AuthenticationAccount:
    return AuthenticationAccount(
        account_id="account-1",
        identity_subject="subject-1",
        normalized_email=NormalizedEmail.from_raw("user@example.com"),
        display_name="Test User",
        user_code="USR-1",
        status=AuthenticationAccountStatus.ACTIVE,
        version=1,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestAuthComposition(unittest.TestCase):
    @patch("bootstrap.auth_dependency.register_auth_records")
    @patch("bootstrap.auth_dependency.create_client")
    @patch("bootstrap.auth_dependency.TokenValidatorAdapter")
    @patch("bootstrap.auth_dependency.IdentityProviderAdapter")
    @patch("bootstrap.auth_dependency.AuthAccountRepositoryAdapter")
    def test_resolver_validates_session_with_request_scoped_session(
        self,
        account_repository_class,
        provider_adapter_class,
        token_validator_class,
        create_client,
        _register_auth_records,
    ):
        database_session = MagicMock()
        provider_client = create_client.return_value
        token_validator_class.return_value.resolve_identity.return_value = (
            AuthenticatedIdentity(subject="subject-1", session_id="session-1")
        )
        account_repository_class.return_value.find_by_subject.return_value = (
            _active_account()
        )
        provider_adapter_class.return_value.has_active_session.return_value = True

        resolver, _ = compose_auth(
            _settings(),
            session_dependency(lambda: database_session),
        )

        app = FastAPI()
        entered: list[str] = []

        @app.get("/probe")
        def probe(
            identity: Annotated[AuthenticatedIdentity, Depends(resolver)],
        ) -> dict[str, str]:
            entered.append(identity.subject)
            return {"subject": identity.subject}

        response = TestClient(app).get("/probe")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"subject": "subject-1"})
        self.assertEqual(entered, ["subject-1"])
        provider_adapter_class.assert_called_once_with(
            provider_client,
            database_session,
        )
        account_repository_class.assert_called_once_with(database_session)
        provider_adapter_class.return_value.has_active_session.assert_called_once_with(
            session_id="session-1",
            subject="subject-1",
        )


if __name__ == "__main__":
    unittest.main()

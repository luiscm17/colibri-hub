"""Local proof that provider session revocation is session-scoped."""

import base64
import json
import unittest
from pathlib import Path
from uuid import uuid4

from auth.adapters.identity_provider.admin_client import IdentityProviderAdapter
from infra.configuration import ApplicationSettings
from sqlalchemy.orm import Session

from backend.integration_tests.database_test_support import (
    test_engine,
    validated_test_database_url,
)
from supabase import create_client


class IdentityProviderSessionPersistenceIntegrationTests(unittest.TestCase):
    """Exercise provider-backed session persistence against the guarded local stack."""

    @classmethod
    def setUpClass(cls) -> None:
        validated_test_database_url()
        cls.engine = test_engine()
        settings = ApplicationSettings.from_environment(Path("backend/.env"))
        assert settings.auth_provider is not None
        cls.url = settings.auth_provider.url
        cls.service_role_key = settings.auth_provider.service_role_key.get_secret_value()

    def test_revokes_only_the_target_session_and_reports_active_state(self) -> None:
        email = f"session-persistence-{uuid4().hex}@example.invalid"
        password = "SyntheticSessionPass1!"
        creation_session = Session(self.engine)
        adapter = IdentityProviderAdapter(
            create_client(self.url, self.service_role_key), creation_session
        )
        identity = None

        try:
            identity = adapter.create_user(email=email, password=password)
            session_a = self._sign_in_and_get_session_id(email, password)
            session_b = self._sign_in_and_get_session_id(email, password)
            self.assertNotEqual(session_a, session_b)

            self.assertTrue(
                adapter.has_active_session(
                    session_id=session_a, subject=identity.subject
                )
            )
            self.assertTrue(
                adapter.has_active_session(
                    session_id=session_b, subject=identity.subject
                )
            )

            adapter.revoke_session(session_id=session_a, subject=identity.subject)
            creation_session.commit()

            verification_session = Session(self.engine)
            try:
                verification_adapter = IdentityProviderAdapter(
                    create_client(self.url, self.service_role_key), verification_session
                )
                self.assertFalse(
                    verification_adapter.has_active_session(
                        session_id=session_a, subject=identity.subject
                    )
                )
                self.assertTrue(
                    verification_adapter.has_active_session(
                        session_id=session_b, subject=identity.subject
                    )
                )
            finally:
                verification_session.rollback()
                verification_session.close()
        finally:
            creation_session.rollback()
            creation_session.close()
            if identity is not None:
                cleanup_session = Session(self.engine)
                try:
                    IdentityProviderAdapter(
                        create_client(self.url, self.service_role_key), cleanup_session
                    ).delete_user(subject=identity.subject)
                finally:
                    cleanup_session.rollback()
                    cleanup_session.close()

    def _sign_in_and_get_session_id(self, email: str, password: str) -> str:
        response = create_client(self.url, self.service_role_key).auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        self.assertIsNotNone(response.session)
        session = response.session
        assert session is not None
        return self._session_id_from_access_token(session.access_token)

    @staticmethod
    def _session_id_from_access_token(access_token: str) -> str:
        payload = access_token.split(".")[1]
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        session_id = json.loads(decoded)["session_id"]
        if not isinstance(session_id, str) or not session_id:
            raise AssertionError("Provider sign-in did not return a session identifier.")
        return session_id


if __name__ == "__main__":
    unittest.main()

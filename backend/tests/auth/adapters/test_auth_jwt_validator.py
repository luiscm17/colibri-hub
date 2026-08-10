"""Unit tests for JWT token validation adapter."""

import time
import unittest
from unittest.mock import MagicMock

import jwt as pyjwt
from auth.adapters.identity_provider.jwt_validator import TokenValidatorAdapter
from auth.domain.errors import AuthenticationRequired

TEST_SECRET = "test-secret-with-at-least-32-characters-long"


class TestJwtValidatorAdapter(unittest.TestCase):
    """JWT validation: signature, expiration, claims extraction."""

    def setUp(self):
        self.validator = TokenValidatorAdapter(jwt_secret=TEST_SECRET)

    def _make_request(self, token: str | None = None) -> MagicMock:
        request = MagicMock()
        if token is None:
            request.headers = {}
        else:
            request.headers = {"authorization": f"Bearer {token}"}
        return request

    def _make_token(self, claims: dict | None = None, secret: str = TEST_SECRET) -> str:
        payload = {
            "sub": "user-subject-123",
            "session_id": "session-456",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "iss": "supabase-demo",
        }
        if claims:
            payload.update(claims)
        return pyjwt.encode(payload, secret, algorithm="HS256")

    def test_valid_token_returns_identity(self):
        token = self._make_token()
        request = self._make_request(token)
        identity = self.validator.resolve_identity(request)
        self.assertEqual(identity.subject, "user-subject-123")
        self.assertEqual(identity.session_id, "session-456")

    def test_missing_authorization_header_raises(self):
        request = self._make_request(None)
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_empty_bearer_token_raises(self):
        request = MagicMock()
        request.headers = {"authorization": "Bearer "}
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_non_bearer_scheme_raises(self):
        request = MagicMock()
        request.headers = {"authorization": "Basic abc123"}
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_expired_token_raises(self):
        token = self._make_token({"exp": int(time.time()) - 100})
        request = self._make_request(token)
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_wrong_secret_raises(self):
        token = self._make_token(secret="different-secret-entirely-wrong-one")
        request = self._make_request(token)
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_malformed_token_raises(self):
        request = self._make_request("not-a-valid-jwt")
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_missing_sub_claim_raises(self):
        token = self._make_token({"sub": ""})
        request = self._make_request(token)
        with self.assertRaises(AuthenticationRequired):
            self.validator.resolve_identity(request)

    def test_no_session_id_returns_none_session(self):
        payload = {
            "sub": "user-no-session",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }
        token = pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")
        request = self._make_request(token)
        identity = self.validator.resolve_identity(request)
        self.assertEqual(identity.subject, "user-no-session")
        self.assertIsNone(identity.session_id)

    def test_issuer_validation_when_configured(self):
        validator = TokenValidatorAdapter(
            jwt_secret=TEST_SECRET, issuer="expected-issuer"
        )
        token = self._make_token({"iss": "wrong-issuer"})
        request = self._make_request(token)
        with self.assertRaises(AuthenticationRequired):
            validator.resolve_identity(request)

    def test_valid_issuer_passes(self):
        validator = TokenValidatorAdapter(
            jwt_secret=TEST_SECRET, issuer="supabase-demo"
        )
        token = self._make_token({"iss": "supabase-demo"})
        request = self._make_request(token)
        identity = validator.resolve_identity(request)
        self.assertEqual(identity.subject, "user-subject-123")


if __name__ == "__main__":
    unittest.main()

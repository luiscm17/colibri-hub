"""JWT token validation adapter producing AuthenticatedIdentity.

Validates Bearer tokens using the provider's JWKS endpoint (ES256) or
a shared HMAC secret (HS256 for legacy/test). Returns a provider-neutral
AuthenticatedIdentity.
"""

from __future__ import annotations

import logging
import time
from threading import Lock

import jwt
from jwt import PyJWKClient
from fastapi import Request

from auth.domain.errors import AuthenticationRequired
from warehouse.bales.ports.authorization import AuthenticatedIdentity

logger = logging.getLogger(__name__)


class TokenValidatorAdapter:
    """Validate provider-issued tokens and produce AuthenticatedIdentity.

    Supports two modes:
    - JWKS (ES256): fetches public keys from the provider's JWKS endpoint.
      Used by default when jwks_url is provided.
    - HMAC (HS256): uses a shared secret. Legacy/test mode when jwks_url is None.

    JWKS keys are cached with a bounded TTL and refreshed on unknown kid.
    """

    def __init__(
        self,
        *,
        jwt_secret: str | None = None,
        jwks_url: str | None = None,
        algorithms: list[str] | None = None,
        issuer: str | None = None,
        audience: str | None = None,
        jwks_cache_ttl: int = 300,
    ) -> None:
        self._secret = jwt_secret
        self._jwks_url = jwks_url
        self._algorithms = algorithms or (["ES256"] if jwks_url else ["HS256"])
        self._issuer = issuer
        self._audience = audience
        self._jwks_client: PyJWKClient | None = None
        self._jwks_cache_ttl = jwks_cache_ttl

        if jwks_url:
            self._jwks_client = PyJWKClient(
                jwks_url, cache_keys=True, lifespan=jwks_cache_ttl
            )

    def resolve_identity(self, request: Request) -> AuthenticatedIdentity:
        """Extract and validate Bearer token from the Authorization header.

        Returns AuthenticatedIdentity on success. Raises AuthenticationRequired
        on any validation failure — no details are exposed about why.
        """
        token = self._extract_token(request)
        claims = self._validate_token(token)

        subject = claims.get("sub")
        if not subject or not isinstance(subject, str):
            raise AuthenticationRequired()

        session_id = claims.get("session_id")
        if isinstance(session_id, str) and session_id:
            return AuthenticatedIdentity(subject=subject, session_id=session_id)

        return AuthenticatedIdentity(subject=subject, session_id=None)

    def _extract_token(self, request: Request) -> str:
        """Extract Bearer token from Authorization header."""
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise AuthenticationRequired()

        parts = auth_header.split(" ", maxsplit=1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationRequired()

        token = parts[1].strip()
        if not token:
            raise AuthenticationRequired()

        return token

    def _validate_token(self, token: str) -> dict:
        """Validate JWT signature, expiration, issuer, and audience."""
        try:
            options: dict = {}
            kwargs: dict = {"algorithms": self._algorithms, "options": options}

            if self._issuer:
                kwargs["issuer"] = self._issuer
            else:
                options["verify_iss"] = False

            if self._audience:
                kwargs["audience"] = self._audience
            else:
                options["verify_aud"] = False

            # JWKS mode: resolve signing key from JWKS endpoint
            if self._jwks_client:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(token, signing_key.key, **kwargs)

            # HMAC mode: use shared secret
            if self._secret:
                return jwt.decode(token, self._secret, **kwargs)

            raise AuthenticationRequired()

        except jwt.ExpiredSignatureError:
            raise AuthenticationRequired()
        except jwt.InvalidTokenError:
            raise AuthenticationRequired()
        except Exception:
            raise AuthenticationRequired()

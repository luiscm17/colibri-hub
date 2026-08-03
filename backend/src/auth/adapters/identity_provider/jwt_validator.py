"""JWT token validation adapter producing AuthenticatedIdentity.

Validates Bearer tokens using the Supabase JWT secret (HS256 for local,
RS256/JWKS for production). Returns a provider-neutral AuthenticatedIdentity.
"""

from __future__ import annotations

import logging

import jwt
from fastapi import Request

from auth.domain.errors import AuthenticationRequired
from warehouse.bales.ports.authorization import AuthenticatedIdentity

logger = logging.getLogger(__name__)


class TokenValidatorAdapter:
    """Validate provider-issued tokens and produce AuthenticatedIdentity.

    For local development, uses the shared HMAC secret (HS256).
    The same adapter can be extended for production JWKS (RS256) by
    fetching keys from the provider's JWKS endpoint.
    """

    def __init__(
        self,
        *,
        jwt_secret: str,
        algorithms: list[str] | None = None,
        issuer: str | None = None,
        audience: str | None = None,
    ) -> None:
        self._secret = jwt_secret
        self._algorithms = algorithms or ["HS256"]
        self._issuer = issuer
        self._audience = audience

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
            kwargs: dict = {
                "algorithms": self._algorithms,
                "options": options,
            }

            if self._issuer:
                kwargs["issuer"] = self._issuer
            else:
                options["verify_iss"] = False

            if self._audience:
                kwargs["audience"] = self._audience
            else:
                options["verify_aud"] = False

            return jwt.decode(token, self._secret, **kwargs)

        except jwt.ExpiredSignatureError:
            raise AuthenticationRequired()
        except jwt.InvalidTokenError:
            raise AuthenticationRequired()
        except Exception:
            raise AuthenticationRequired()

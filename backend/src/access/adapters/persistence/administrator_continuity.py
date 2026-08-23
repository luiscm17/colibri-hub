"""PostgreSQL adapter for the Access-owned administrator continuity policy."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from access.domain.errors import AdministratorContinuityRequired


class AdministratorContinuityAdapter:
    """Serialize reducing mutations and evaluate their cross-context projection."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def assert_reduction_allowed(self, subject: str) -> None:
        enabled = self._session.execute(
            text(
                "select enforcement_enabled "
                "from access_administrator_continuity where id = 1 for update"
            )
        ).scalar_one()
        if not enabled:
            return

        remaining = self._session.execute(
            text(
                "select count(distinct au.identity_subject) "
                "from authentication_accounts aa "
                "join access_users au on au.identity_subject = aa.identity_subject::text "
                "join access_user_role_assignments aura "
                "on aura.user_id = au.user_id and aura.revoked_at is null "
                "join access_roles ar "
                "on ar.role_id = aura.role_id and ar.is_system_administrator "
                "where aa.status = 'active' and au.is_active "
                "and au.identity_subject != :subject"
            ),
            {"subject": subject},
        ).scalar_one()
        if remaining < 2:
            raise AdministratorContinuityRequired()

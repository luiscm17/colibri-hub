"""Tests for C4: AccessProvisioningAdapter passes correct display_name.

Validates that provision_profile uses the display_name parameter
instead of substituting profile_code.
"""

import unittest
from unittest.mock import MagicMock

from access.adapters.access_provisioning import AccessProvisioningAdapter
from access.application.commands import CreateAccessUserCommand


class TestAccessProvisioningDisplayName(unittest.TestCase):
    """C4: provisioning uses correct display_name."""

    def test_provision_profile_passes_display_name(self):
        create_user = MagicMock()
        activate_user = MagicMock()
        deactivate_user = MagicMock()
        user_repository = MagicMock()

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            user_repository=user_repository,
        )

        adapter.provision_profile(
            subject="sub-123",
            profile_code="USR-015",
            display_name="María García",
            role_codes=["system_administrator"],
            actor_subject="actor-sub",
            reason="Test provisioning",
            operation_id="op-001",
        )

        create_user.execute.assert_called_once()
        call_args = create_user.execute.call_args[0][0]
        self.assertIsInstance(call_args, CreateAccessUserCommand)
        self.assertEqual(call_args.display_name, "María García")
        self.assertEqual(call_args.user_code, "USR-015")

    def test_provision_profile_falls_back_to_profile_code_when_empty(self):
        create_user = MagicMock()
        activate_user = MagicMock()
        deactivate_user = MagicMock()
        user_repository = MagicMock()

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            user_repository=user_repository,
        )

        adapter.provision_profile(
            subject="sub-123",
            profile_code="USR-015",
            display_name="",
            role_codes=["warehouse_reader"],
            actor_subject="actor-sub",
            reason="Test provisioning",
            operation_id="op-002",
        )

        call_args = create_user.execute.call_args[0][0]
        self.assertEqual(call_args.display_name, "USR-015")

    def test_would_remove_last_administrator_uses_for_update(self):
        """C3: would_remove_last_administrator calls count_active_administrators with for_update=True."""
        create_user = MagicMock()
        activate_user = MagicMock()
        deactivate_user = MagicMock()
        user_repository = MagicMock()

        user_repository.find_by_subject.return_value = MagicMock(user_id="uid-1")
        user_repository.count_active_administrators.return_value = 0

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            user_repository=user_repository,
        )

        result = adapter.would_remove_last_administrator("sub-123")

        self.assertTrue(result)
        user_repository.count_active_administrators.assert_called_once_with(
            exclude_user_id="uid-1", for_update=True
        )


if __name__ == "__main__":
    unittest.main()

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
        continuity = MagicMock()
        continuity.assert_reduction_allowed = MagicMock()

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            continuity=continuity,
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
        continuity = MagicMock()

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            continuity=continuity,
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

    def test_assert_reduction_allowed_delegates_to_access_continuity(self):
        create_user = MagicMock()
        activate_user = MagicMock()
        deactivate_user = MagicMock()
        continuity = MagicMock()
        continuity.assert_reduction_allowed = MagicMock()

        adapter = AccessProvisioningAdapter(
            create_user=create_user,
            activate_user=activate_user,
            deactivate_user=deactivate_user,
            continuity=continuity,
        )

        adapter.assert_reduction_allowed("sub-123")

        continuity.assert_reduction_allowed.assert_called_once_with("sub-123")


if __name__ == "__main__":
    unittest.main()

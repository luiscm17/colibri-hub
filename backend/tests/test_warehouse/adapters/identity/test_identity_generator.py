import unittest
from uuid import UUID

from warehouse.adapters.identity.uuid_identity_generator import (
    UuidIdentityGenerator as LegacyUuidIdentityGenerator,
)
from warehouse.bales.adapters.identity.identity_generator import UuidIdentityGenerator
from warehouse.bales.ports.identity_generator import IdentityGenerator


class TestUuidIdentityGenerator(unittest.TestCase):
    def test_canonical_and_legacy_imports_are_the_same_class(self) -> None:
        self.assertIs(LegacyUuidIdentityGenerator, UuidIdentityGenerator)

    def test_generates_a_uuid_that_satisfies_the_canonical_port(self) -> None:
        generator = UuidIdentityGenerator()

        self.assertIsInstance(generator, IdentityGenerator)
        self.assertIsInstance(generator.next_id(), UUID)


if __name__ == "__main__":
    unittest.main()

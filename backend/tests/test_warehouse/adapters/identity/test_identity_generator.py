import unittest
from uuid import UUID

from warehouse.bales.adapters.identity.identity_generator import Uuid4IdentityGenerator
from warehouse.bales.ports.identity_generator import IdentityGenerator


class TestUuid4IdentityGenerator(unittest.TestCase):
    def test_generates_a_uuid_that_satisfies_the_canonical_port(self) -> None:
        generator = Uuid4IdentityGenerator()

        self.assertIsInstance(generator, IdentityGenerator)
        self.assertIsInstance(generator.next_id(), UUID)


if __name__ == "__main__":
    unittest.main()

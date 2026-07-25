from uuid import UUID, uuid4

from warehouse.bales.ports.identity_generator import IdentityGenerator


class Uuid4IdentityGenerator(IdentityGenerator):
    def next_id(self) -> UUID:
        return uuid4()

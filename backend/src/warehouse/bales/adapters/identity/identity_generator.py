from uuid import UUID, uuid4

from warehouse.bales.ports.identity_generator import IdentityGenerator


class Uuid4IdentityGenerator(IdentityGenerator):
    """Generates technical identities using UUID v4."""
    
    def next_id(self) -> UUID:
        """Generate a new UUID v4."""
        return uuid4()

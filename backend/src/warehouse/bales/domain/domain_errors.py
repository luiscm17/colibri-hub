class DomainError(Exception):
    """Base exception for warehouse domain rule violations."""


class InvalidBaleNumberError(DomainError): pass
class InvalidMaterialTypeError(DomainError): pass
class InvalidBaleWeightError(DomainError): pass
class InvalidBaleStateTransitionError(DomainError): pass
class InvalidDtexError(DomainError): pass
class InvalidShipmentNumberError(DomainError): pass
class InvalidReceptionDateTimeError(DomainError): pass
class InvalidReceptionDateError(DomainError): pass
class InvalidDeliveryDateError(DomainError): pass
class EmptyRawMaterialBatchError(DomainError): pass
class DuplicateBaleIdError(DomainError): pass
class InvalidProviderNameError(DomainError): pass
class ExcessiveBatchSizeError(DomainError): pass
class InvalidBaleStateDateCombinationError(DomainError): pass

class UnexpectedError(Exception):
    ...

class AbstractError(Exception):
    ...

class NoPromisedValidator(AbstractError):
    ...

class FieldRequirementException(Exception):
    ...

class ValidationError(Exception):
    ...

class NativeValidationError(ValidationError):
    ...

class NotNoneError(NativeValidationError):
    ...
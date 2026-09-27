"""bhairava.exceptions -- Typed exceptions mapped to exit codes."""
class BhairavaError(Exception):
    """Base class. exit_code defaults to 1."""
    exit_code = 1


class ConfigError(BhairavaError):
    exit_code = 2


class ScopeViolation(BhairavaError):
    exit_code = 3


class MissingDependency(BhairavaError):
    exit_code = 4


class ValidationFailure(BhairavaError):
    exit_code = 5

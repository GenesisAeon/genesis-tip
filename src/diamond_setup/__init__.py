"""Diamond Setup — scaffold + GenesisAeon Diamond interface contract."""

from diamond_setup.protocol import (
    CREPState,
    DiamondPackage,
    DiamondProtocol,
    NotConvergedError,
    NotInitializedError,
    ResilienceState,
    UTACState,
    ZenodoRecord,
)
from diamond_setup.validation import check_diamond_class, validate_diamond_instance

__version__ = "2.2.0"
__author__ = "GenesisAeon"

__all__ = [
    "CREPState",
    "DiamondPackage",
    "DiamondProtocol",
    "NotConvergedError",
    "NotInitializedError",
    "ResilienceState",
    "UTACState",
    "ZenodoRecord",
    "__version__",
    "check_diamond_class",
    "validate_diamond_instance",
]

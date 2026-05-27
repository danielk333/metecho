try:
    # Python StrEnum has default lowercase for auto() but is only available from py 3.11
    from enum import StrEnum
except ImportError:
    from strenum import (  # type: ignore[assignment, no-redef, unused-ignore, import-not-found]
        LowercaseStrEnum as StrEnum,  # type: ignore[import-not-found,no-redef, unused-ignore]
    )


class MeteorType(StrEnum):
    head = "head"
    trail = "trail"

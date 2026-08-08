from app.schemas.session import Level
from app.schemas.topic_plan import Depth

_ORDER: tuple[Level, ...] = ("foundational", "intermediate", "advanced")


def increase(level: Level) -> Level:
    """Move one step up the difficulty scale; already at max stays put."""
    try:
        index = _ORDER.index(level)
    except ValueError:
        return level
    return _ORDER[min(index + 1, len(_ORDER) - 1)]


def decrease(level: Level) -> Level:
    """Move one step down the difficulty scale (diagnostic/foundational probe); floor at min."""
    try:
        index = _ORDER.index(level)
    except ValueError:
        return level
    return _ORDER[max(index - 1, 0)]


def base_level(depth: Depth) -> Level:
    """Initial difficulty for a planned topic, derived from candidate evidence depth."""
    if depth == "high":
        return "intermediate"
    return "foundational"

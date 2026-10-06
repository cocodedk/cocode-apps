"""A check returns Gaps: what an app lacks against the standard."""
from collections.abc import Callable
from dataclasses import dataclass

Fetch = Callable[[str], tuple[int, str]]


@dataclass(frozen=True)
class Gap:
    app: str
    area: str
    message: str

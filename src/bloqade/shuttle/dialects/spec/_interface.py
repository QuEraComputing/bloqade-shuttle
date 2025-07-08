from typing import Any

from bloqade.geometry.dialects import grid
from kirin.lowering import wraps as _wraps

from bloqade.shuttle.arch import ArchSpec as ArchSpec, Layout as Layout

from .stmts import GetStaticTrap


@_wraps(GetStaticTrap)
def get_static_trap(*, zone_id: str) -> grid.Grid[Any, Any]: ...

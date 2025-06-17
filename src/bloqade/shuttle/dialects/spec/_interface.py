from typing import Any

from bloqade.geometry.dialects import grid
from kirin.lowering import wraps as _wraps

from .stmts import GetStaticTrap
from .types import Layout as Layout, Spec as Spec


@_wraps(GetStaticTrap)
def get_static_trap(*, zone_id: str) -> grid.Grid[Any, Any]: ...

from typing import Any

from bloqade.geometry.dialects import grid
from kirin.lowering import wraps as _wraps

from bloqade.shuttle.arch import ArchSpec as ArchSpec, Layout as Layout

from .stmts import GetFloatConstant, GetIntConstant, GetSpecialGrid, GetStaticTrap


@_wraps(GetStaticTrap)
def get_static_trap(*, zone_id: str) -> grid.Grid[Any, Any]:
    """Get a static trap by its zone ID."""
    ...


@_wraps(GetSpecialGrid)
def get_special_grid(*, grid_id: str) -> grid.Grid[Any, Any]:
    """Get a special grid by its ID."""
    ...


@_wraps(GetIntConstant)
def get_int_constant(*, constant_id: str) -> int: ...


@_wraps(GetFloatConstant)
def get_float_constant(*, constant_id: str) -> float: ...

from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import Fill, GetParent, Vacate
from .types import FilledGrid

Nx = TypeVar("Nx")
Ny = TypeVar("Ny")


@_wraps(Vacate)
def vacate(
    zone: grid.Grid[Nx, Ny],
    vacancies: ilist.IList[tuple[int, int], Any],
) -> FilledGrid[Nx, Ny]: ...


@_wraps(Fill)
def fill(
    zone: grid.Grid[Nx, Ny],
    filled: ilist.IList[tuple[int, int], Any],
) -> FilledGrid[Nx, Ny]: ...


@_wraps(GetParent)
def get_parent(filled_grid: FilledGrid[Nx, Ny]) -> grid.Grid[Nx, Ny]: ...


@_wraps(grid.Shift)
def shift(
    grid: FilledGrid[Nx, Ny], x_shift: float, y_shift: float
) -> FilledGrid[Nx, Ny]: ...


@_wraps(grid.Scale)
def scale(
    grid: FilledGrid[Nx, Ny], x_scale: float, y_scale: float
) -> FilledGrid[Nx, Ny]: ...


@_wraps(grid.Repeat)
def repeat(
    grid: FilledGrid[Any, Any],
    x_times: int,
    y_times: int,
    y_spacing: float,
    x_spacing: float,
) -> FilledGrid[Any, Any]: ...

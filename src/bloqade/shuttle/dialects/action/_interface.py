from typing import Any, TypeVar, overload

from bloqade.geometry.dialects.grid import Grid
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import Move, Set, TurnOff, TurnOn


@overload
def turn_on(x_tones: slice, y_tones: slice) -> None: ...
@overload
def turn_on(x_tones: slice, y_tones: ilist.IList[int, Any] | list[int]) -> None: ...
@overload
def turn_on(x_tones: ilist.IList[int, Any] | list[int], y_tones: slice) -> None: ...
@overload
def turn_on(
    x_tones: ilist.IList[int, Any] | list[int],
    y_tones: ilist.IList[int, Any] | list[int],
) -> None: ...
@_wraps(TurnOn)
def turn_on(x_tones, y_tones):
    """Turn on tones at the given x and y locations."""


@overload
def turn_off(x_tones: slice, y_tones: slice) -> None: ...
@overload
def turn_off(x_tones: slice, y_tones: ilist.IList[int, Any] | list[int]) -> None: ...
@overload
def turn_off(x_tones: ilist.IList[int, Any] | list[int], y_tones: slice) -> None: ...
@overload
def turn_off(
    x_tones: ilist.IList[int, Any] | list[int],
    y_tones: ilist.IList[int, Any] | list[int],
) -> None: ...
@_wraps(TurnOff)
def turn_off(x_tones, y_tones):
    """Turn on tones at the given x and y locations."""


Nx = TypeVar("Nx")
Ny = TypeVar("Ny")


@_wraps(Set)
def set_loc(grid: Grid[Nx, Ny]) -> None:
    """Set the location of the aod using a grid."""


@_wraps(Move)
def move(grid: Grid[Nx, Ny]) -> None:
    """Move the aod from its current location to the given location."""


ALL = slice(None)

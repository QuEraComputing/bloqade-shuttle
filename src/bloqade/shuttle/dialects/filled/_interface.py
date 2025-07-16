from typing import TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import Fill, GetParent, Vacat
from .types import FilledGrid

NumX = TypeVar("NumX")
NumY = TypeVar("NumY")
NumVacant = TypeVar("NumVacant")


@_wraps(Vacat)
def vacat(
    zone: grid.Grid[NumX, NumY],
    vacant: ilist.IList[tuple[int, int], NumVacant],
) -> FilledGrid[NumX, NumY]: ...


@_wraps(Fill)
def fill(
    zone: grid.Grid[NumX, NumY],
    filled_x: ilist.IList[tuple[int, int], NumVacant],
) -> FilledGrid[NumX, NumY]: ...


@_wraps(GetParent)
def get_parent(filled_grid: FilledGrid[NumX, NumY]) -> grid.Grid[NumX, NumY]: ...

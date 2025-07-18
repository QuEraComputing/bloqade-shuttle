from typing import Any

from bloqade.geometry.dialects.grid.types import Grid
from kirin.dialects import ilist
from kirin.interp import (
    Frame,
    Interpreter,
    MethodTable,
    impl,
)

from . import stmts
from ._dialect import dialect
from .types import FilledGrid


@dialect.register
class FilledGridMethods(MethodTable):

    @impl(stmts.Vacate)
    def vacate(self, interp: Interpreter, frame: Frame, stmt: stmts.Vacate):
        zone = frame.get_casted(stmt.zone, Grid)
        vacancies = frame.get_casted(stmt.vacancies, ilist.IList[tuple[int, int], Any])
        return (FilledGrid.vacate(zone, vacancies),)

    @impl(stmts.Fill)
    def fill(self, interp: Interpreter, frame: Frame, stmt: stmts.Fill):
        zone = frame.get_casted(stmt.zone, Grid)
        filled = frame.get_casted(stmt.filled, ilist.IList[tuple[int, int], Any])
        return (FilledGrid.fill(zone, filled),)

    @impl(stmts.GetParent)
    def get_parent(self, interp: Interpreter, frame: Frame, stmt: stmts.GetParent):
        filled_grid = frame.get_casted(stmt.filled_grid, FilledGrid)
        return (filled_grid.parent,)

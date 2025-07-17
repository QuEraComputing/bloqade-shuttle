from bloqade.geometry.dialects import grid
from kirin import decl, ir, lowering, types
from kirin.decl import info
from kirin.dialects import ilist

from ._dialect import dialect
from .types import FilledGridType

NumVacant = types.TypeVar("NumVacant")
Nx = types.TypeVar("Nx")
Ny = types.TypeVar("Ny")


@decl.statement(dialect=dialect)
class Vacate(ir.Statement):
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    zone: ir.SSAValue = info.argument(grid.GridType[Nx, Ny])
    vacancies: ir.SSAValue = info.argument(
        ilist.IListType[types.Tuple[types.Int, types.Int], NumVacant]
    )
    result: ir.ResultValue = info.result(FilledGridType[Nx, Ny])


@decl.statement(dialect=dialect)
class Fill(ir.Statement):
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    zone: ir.SSAValue = info.argument(grid.GridType[Nx, Ny])
    filled: ir.SSAValue = info.argument(
        ilist.IListType[types.Tuple[types.Int, types.Int], NumVacant]
    )
    result: ir.ResultValue = info.result(FilledGridType[Nx, Ny])


@decl.statement(dialect=dialect)
class GetParent(ir.Statement):
    name = "get_parent"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})

    filled_grid: ir.SSAValue = info.argument(FilledGridType[Nx, Ny])
    result: ir.ResultValue = info.result(grid.GridType[Nx, Ny])

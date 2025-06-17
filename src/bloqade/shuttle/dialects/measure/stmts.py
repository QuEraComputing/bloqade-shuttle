from typing import cast

from bloqade.geometry.dialects import grid
from kirin import decl, ir, lowering, types
from kirin.decl import info
from kirin.dialects import ilist

from ._dialect import dialect
from .types import MeasurementArrayType, MeasurementResultType

NumX = types.TypeVar("NumX")
NumY = types.TypeVar("NumY")

MeasureReturnType = types.Tuple[types.Vararg(MeasurementArrayType[NumX, NumY])]


@decl.statement(dialect=dialect)
class Measure(ir.Statement):
    name = "measure"

    traits = frozenset({lowering.FromPythonCall()})

    grids: tuple[ir.SSAValue, ...] = info.argument(grid.GridType[NumX, NumY])

    def __init__(self, grids: tuple[ir.SSAValue, ...]):
        result_types = []

        for grid_ssa in grids:
            grid_type = grid_ssa.type
            if (grid_type := cast(types.Generic, grid_type)).is_subseteq(grid.GridType):
                NumX, NumY = grid_type.vars
            else:
                NumX, NumY = types.Any, types.Any

            result_types.append(MeasurementArrayType[NumX, NumY])

        super().__init__(
            args=grids,
            result_types=tuple(result_types),
            args_slice={
                "grids": slice(0, len(grids)),
            },
        )


L = types.TypeVar("L")


@decl.statement(dialect=dialect)
class New(ir.Statement):
    name = "new"

    traits = frozenset({lowering.FromPythonCall(), ir.Pure()})

    num_rows: ir.SSAValue = info.argument(
        NumRows := types.TypeVar("NumRows", bound=types.Int)
    )
    num_cols: ir.SSAValue = info.argument(
        NumCols := types.TypeVar("NumCols", bound=types.Int)
    )
    values: ir.SSAValue = info.argument(ilist.IListType[MeasurementResultType, L])
    result: ir.ResultValue = info.result(MeasurementArrayType[NumRows, NumCols])

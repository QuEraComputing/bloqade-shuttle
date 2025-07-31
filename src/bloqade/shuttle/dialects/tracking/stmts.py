from typing import cast

from bloqade.geometry.dialects import grid
from kirin import ir, types
from kirin.decl import info, statement
from kirin.dialects import ilist

from .. import measure, path as path_dialect
from ._dialect import dialect
from .types import SystemStateType


@statement(dialect=dialect)
class Fill(ir.Statement):
    name = "fill"

    traits = frozenset({})

    locations: ir.SSAValue = info.argument(
        ilist.IListType[grid.GridType[types.Any, types.Any], types.Any]
    )
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class Play(ir.Statement):
    name = "play"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    path: ir.SSAValue = info.argument(path_dialect.PathType)
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class TopHatCZ(ir.Statement):
    name = "tophat_cz"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class GlobalR(ir.Statement):
    name = "global_r"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    axis_angle: ir.SSAValue = info.argument(types.Float)
    rotation_angle: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class LocalR(ir.Statement):
    name = "local_r"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    axis_angle: ir.SSAValue = info.argument(types.Float)
    rotation_angle: ir.SSAValue = info.argument(types.Float)
    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class GlobalRz(ir.Statement):
    name = "global_rz"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    rotation_angle: ir.SSAValue = info.argument(types.Float)
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class LocalRz(ir.Statement):
    name = "local_rz"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    rotation_angle: ir.SSAValue = info.argument(types.Float)
    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    result: ir.ResultValue = info.result(SystemStateType)


@statement(dialect=dialect)
class Measure(ir.Statement):
    name = "measure"

    traits = frozenset({})

    state: ir.SSAValue = info.argument(SystemStateType)
    grids: tuple[ir.SSAValue, ...] = info.argument(grid.GridType[types.Any, types.Any])

    def __init__(self, state: ir.SSAValue, grids: tuple[ir.SSAValue, ...]):
        result_types: list[types.TypeAttribute] = [SystemStateType]

        for grid_ssa in grids:
            grid_type = grid_ssa.type
            if (grid_type := cast(types.Generic, grid_type)).is_subseteq(grid.GridType):
                NumX, NumY = grid_type.vars
            else:
                NumX, NumY = types.Any, types.Any

            result_types.append(measure.MeasurementArrayType[NumX, NumY])

        super().__init__(
            args=(state,) + grids,
            result_types=tuple(result_types),
            args_slice={"state": 0, "grids": slice(1, len(grids) + 1)},
        )

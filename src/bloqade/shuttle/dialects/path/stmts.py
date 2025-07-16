from typing import Optional

from kirin import decl, ir
from kirin.decl import info

from bloqade.shuttle.arch import ArchSpec
from bloqade.shuttle.dialects import schedule

from ._dialect import dialect
from .types import PathType


@decl.statement(dialect=dialect)
class Gen(ir.Statement):
    name = "gen"

    traits = frozenset({ir.Pure()})
    # not a fixed type here so just any
    device_task: ir.SSAValue = info.argument(schedule.DeviceFunctionType)
    arch_spec: Optional[ArchSpec] = info.attribute(default=None)
    inputs: tuple[ir.SSAValue, ...] = info.argument()
    kwargs: tuple[str, ...] = info.attribute(default_factory=lambda: ())
    result: ir.ResultValue = info.result(PathType)


@decl.statement(dialect=dialect)
class Parallel(ir.Statement):
    name = "parallel"

    traits = frozenset({ir.Pure()})
    paths: tuple[ir.SSAValue, ...] = info.argument()
    result: ir.ResultValue = info.result(PathType)

    def __init__(self, paths: tuple[ir.SSAValue, ...]):
        super().__init__(
            args=paths,
            result_types=[PathType],
            args_slice={"paths": slice(0, len(paths), 1)},
        )


@decl.statement(dialect=dialect)
class Auto(ir.Statement):
    name = "auto"

    traits = frozenset({ir.Pure()})
    paths: tuple[ir.SSAValue, ...] = info.argument()
    result: ir.ResultValue = info.result(PathType)

    def __init__(self, paths: tuple[ir.SSAValue, ...]):
        super().__init__(
            args=paths,
            result_types=[PathType],
            args_slice={"paths": slice(0, len(paths), 1)},
        )


@decl.statement(dialect=dialect)
class Play(ir.Statement):
    name = "play"

    traits = frozenset({})
    path: ir.SSAValue = info.argument(PathType)

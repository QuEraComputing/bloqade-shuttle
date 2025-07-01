from kirin import ir, lowering, types
from kirin.decl import info, statement
from kirin.dialects import ilist
from kirin.lowering.python.traits import FromPythonWithSingleItem

from bloqade.shuttle.dialects.schedule._dialect import dialect
from bloqade.shuttle.dialects.schedule.types import TaskType

NxTones = types.TypeVar("NxTones")
NyTones = types.TypeVar("NyTones")


@statement(dialect=dialect)
class NewTweezerTask(ir.Statement):
    name = "tweezer_task"
    traits = frozenset({ir.Pure()})
    move_fn: ir.SSAValue = info.argument(types.MethodType)
    result: ir.ResultValue = info.result(TaskType)


@statement(dialect=dialect)
class NewDeviceFunction(ir.Statement):
    name = "device_function"
    traits = frozenset({lowering.FromPythonCall(), ir.Pure()})
    move_fn: ir.SSAValue = info.argument(types.MethodType)
    x_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, NxTones])
    y_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, NyTones])
    result: ir.ResultValue = info.result(TaskType)


@statement(dialect=dialect)
class Reverse(ir.Statement):
    name = "reverse"
    traits = frozenset({lowering.FromPythonCall(), ir.Pure()})

    device_fn: ir.SSAValue = info.argument(TaskType)
    result: ir.ResultValue = info.result(TaskType)


@statement
class ExecutableRegion(ir.Statement):
    traits = frozenset({FromPythonWithSingleItem()})
    body: ir.Region = info.region(multi=False)


# TODO: implement lowering with captured values
@statement(dialect=dialect)
class Parallel(ExecutableRegion):
    name = "parallel"


# TODO: implement lowering with captured values
@statement(dialect=dialect)
class Auto(ExecutableRegion):
    name = "auto"

from bloqade.geometry.dialects import grid
from kirin import ir, lowering, types
from kirin.decl import info, statement

from bloqade.shuttle.dialects.spec._dialect import dialect


@statement(dialect=dialect)
class GetStaticTrap(ir.Statement):
    name = "get_static_trap"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone_id: str = info.attribute()
    result: ir.ResultValue = info.result(grid.GridType[types.Any, types.Any])


@statement(dialect=dialect)
class GetIntConstant(ir.Statement):
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    constant_id: str = info.attribute()
    result: ir.ResultValue = info.result(types.Int)


@statement(dialect=dialect)
class GetFloatConstant(ir.Statement):
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    constant_id: str = info.attribute()
    result: ir.ResultValue = info.result(types.Float)

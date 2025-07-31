from bloqade.geometry.dialects import grid
from kirin import ir, lowering, types
from kirin.decl import info, statement

from ._dialect import dialect


@statement(dialect=dialect)
class GetStaticTrap(ir.Statement):
    name = "get_static_trap"
    traits = frozenset({ir.Pure(), lowering.FromPythonCall()})
    zone_id: str = info.attribute()
    result: ir.ResultValue = info.result(grid.GridType[types.Any, types.Any])

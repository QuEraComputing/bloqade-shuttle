from bloqade.geometry.dialects import grid
from kirin import decl, ir, lowering, types
from kirin.decl import info
from kirin.dialects import ilist

from ._dialect import dialect


@decl.statement(dialect=dialect)
class Fill(ir.Statement):
    name = "fill"

    traits = frozenset({lowering.FromPythonCall()})
    locations: ir.SSAValue = info.argument(
        ilist.IListType[grid.GridType[types.Any, types.Any], types.Any]
    )

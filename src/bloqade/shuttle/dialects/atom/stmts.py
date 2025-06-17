from bloqade.geometry.dialects import grid
from bloqade.types import QubitType
from kirin import ir, lowering, types
from kirin.decl import info, statement
from kirin.dialects import ilist

from ._dialect import dialect
from .types import AtomType

NumAtoms = types.TypeVar("NumAtoms")


@statement(dialect=dialect)
class New(ir.Statement):
    name = "new"

    traits = frozenset({lowering.FromPythonCall()})

    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    qubits: ir.SSAValue = info.argument(ilist.IListType[QubitType, NumAtoms])
    result: ir.ResultValue = info.result(ilist.IListType[AtomType, NumAtoms])


@statement(dialect=dialect)
class Move(ir.Statement):
    name = "move"

    traits = frozenset({lowering.FromPythonCall(), ir.Pure()})

    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    atoms: ir.SSAValue = info.argument(ilist.IListType[AtomType, NumAtoms])
    result: ir.ResultValue = info.result(ilist.IListType[AtomType, NumAtoms])


@statement(dialect=dialect)
class MoveNextTo(ir.Statement):
    name = "move_next_to"

    traits = frozenset({lowering.FromPythonCall(), ir.Pure()})

    zone: ir.SSAValue = info.argument(grid.GridType[types.Any, types.Any])
    ctrls: ir.SSAValue = info.argument(ilist.IListType[AtomType, NumAtoms])
    qargs: ir.SSAValue = info.argument(ilist.IListType[AtomType, NumAtoms])

    def __init__(self, zone: ir.SSAValue, ctrls: ir.SSAValue, qargs: ir.SSAValue):
        NumAtoms = (
            ctrls.type.vars[1]
            if isinstance(ctrls.type, types.Generic)
            else types.TypeVar("NumAtoms")
        )
        super().__init__(
            args=(zone, ctrls, qargs),
            args_slice={"zone": 0, "ctrls": 1, "qargs": 2},
            result_types=[
                ilist.IListType[AtomType, NumAtoms],
                ilist.IListType[AtomType, NumAtoms],
            ],
        )


@statement(dialect=dialect)
class ResetPosition(ir.Statement):
    name = "reset_position"

    traits = frozenset({lowering.FromPythonCall()})

    atoms: ir.SSAValue = info.argument(ilist.IListType[AtomType, NumAtoms])
    qubits: ir.SSAValue = info.argument(ilist.IListType[QubitType, NumAtoms])


@statement(dialect=dialect)
class Measure(ir.Statement):
    name = "measure"

    traits = frozenset({lowering.FromPythonCall()})

    atoms: ir.SSAValue = info.argument(ilist.IListType[AtomType, NumAtoms])
    qubits: ir.SSAValue = info.argument(ilist.IListType[QubitType, NumAtoms])
    result: ir.ResultValue = info.result(ilist.IListType[types.Int, NumAtoms])

from bloqade.geometry.dialects.grid import GridType
from kirin import decl, ir, lowering, types
from kirin.decl import info

from ._dialect import dialect


@decl.statement(dialect=dialect)
class TopHatCZ(ir.Statement):
    name = "apply"

    traits = frozenset({lowering.FromPythonCall()})
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])
    upper_buffer: float = info.attribute(default=3.0)
    lower_buffer: float = info.attribute(default=3.0)


@decl.statement(dialect=dialect)
class LocalRz(ir.Statement):
    """
    Apply gate op locally
    """

    traits = frozenset({lowering.FromPythonCall()})
    rotation_angle: ir.SSAValue = info.argument(type=types.Float)
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])


@decl.statement(dialect=dialect)
class LocalR(ir.Statement):
    """
    Apply gate op locally
    """

    traits = frozenset({lowering.FromPythonCall()})
    axis_angle: ir.SSAValue = info.argument(type=types.Float)
    rotation_angle: ir.SSAValue = info.argument(type=types.Float)
    zone: ir.SSAValue = info.argument(type=GridType[types.Any, types.Any])


@decl.statement(dialect=dialect)
class GlobalR(ir.Statement):
    """
    Apply gate op globally
    """

    traits = frozenset({lowering.FromPythonCall()})
    axis_angle: ir.SSAValue = info.argument(type=types.Float)
    rotation_angle: ir.SSAValue = info.argument(type=types.Float)


@decl.statement(dialect=dialect)
class GlobalRz(ir.Statement):
    """
    Apply gate op globally
    """

    traits = frozenset({lowering.FromPythonCall()})
    rotation_angle: ir.SSAValue = info.argument(type=types.Float)

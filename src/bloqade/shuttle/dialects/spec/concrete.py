from kirin import interp

from bloqade.shuttle.arch import ArchSpecInterpreter

from ._dialect import dialect
from .stmts import GetFloatConstant, GetIntConstant, GetSpecialGrid, GetStaticTrap


@dialect.register(key="spec.interp")
class ArchSpecMethods(interp.MethodTable):
    @interp.impl(GetStaticTrap)
    def get_static_trap(
        self,
        _interp: ArchSpecInterpreter,
        frame: interp.Frame,
        stmt: GetStaticTrap,
    ):
        if (zone := _interp.arch_spec.layout.static_traps.get(stmt.zone_id)) is None:
            raise interp.InterpreterError(f"Zone {stmt.zone_id} not found in layout.")
        return (zone,)

    @interp.impl(GetSpecialGrid)
    def get_special_grid(
        self,
        _interp: ArchSpecInterpreter,
        frame: interp.Frame,
        stmt: GetSpecialGrid,
    ):
        if (grid := _interp.arch_spec.layout.special_grid.get(stmt.grid_id)) is None:
            raise interp.InterpreterError(
                f"Special grid {stmt.grid_id} not found in layout."
            )
        return (grid,)

    @interp.impl(GetFloatConstant)
    def get_float_constant(
        self,
        _interp: ArchSpecInterpreter,
        frame: interp.Frame,
        stmt: GetFloatConstant,
    ):
        if (const := _interp.arch_spec.float_constants.get(stmt.constant_id)) is None:
            raise interp.InterpreterError(
                f"Float constant {stmt.constant_id} not found in layout."
            )
        return (const,)

    @interp.impl(GetIntConstant)
    def get_int_constant(
        self,
        _interp: ArchSpecInterpreter,
        frame: interp.Frame,
        stmt: GetIntConstant,
    ):
        if (const := _interp.arch_spec.int_constants.get(stmt.constant_id)) is None:
            raise interp.InterpreterError(
                f"Int constant {stmt.constant_id} not found in layout."
            )
        return (const,)

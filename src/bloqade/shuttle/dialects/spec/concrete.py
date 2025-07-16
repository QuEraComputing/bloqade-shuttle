from kirin import interp

from bloqade.shuttle.arch import ArchSpecInterpreter

from ._dialect import dialect
from .stmts import GetStaticTrap


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
            raise interp.InterpreterError("Zone not found in layout.")
        return (zone,)

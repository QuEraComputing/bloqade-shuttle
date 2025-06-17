from kirin.analysis.forward import ForwardFrame
from kirin.interp import MethodTable, impl

from bloqade.shuttle.dialects import spec

from .. import analysis, lattice


@spec.dialect.register(key="zone.analysis")
class SpecImpl(MethodTable):
    @impl(spec.GetStaticTrap)
    def get_static_trap(
        self,
        interp: analysis.ZoneAnalysis,
        frame: ForwardFrame[lattice.Zone],
        stmt: spec.GetStaticTrap,
    ):
        if stmt.zone_id in interp.arch_spec.layout.static_traps:
            return (lattice.SpecZone(stmt.zone_id),)

        return (lattice.InvalidSpecId(stmt.zone_id),)

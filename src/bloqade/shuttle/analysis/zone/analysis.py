from dataclasses import dataclass, field

from bloqade.geometry.dialects import grid
from kirin import interp, ir
from kirin.analysis.forward import Forward, ForwardFrame

from bloqade.shuttle.arch import ArchSpec

from .lattice import SpecZone, UnknownZone, Zone


@dataclass
class ZoneAnalysis(Forward[Zone]):
    """
    Analysis for zones in the Qourier context.
    This analysis extends the Forward analysis to work with Zone types.
    """

    keys = ["zone.analysis"]
    lattice = Zone
    arch_spec: ArchSpec = field(default_factory=ArchSpec)

    def get_grid_lattice(self, zone: grid.Grid) -> Zone:
        for zone_id, zone_obj in self.arch_spec.layout.static_traps.items():
            if zone is zone_obj:  # must be the object defined in the spec to match
                return SpecZone(zone_id)

        return UnknownZone()

    def eval_stmt_fallback(
        self, frame: ForwardFrame[Zone], stmt: ir.Statement
    ) -> tuple[Zone, ...] | interp.SpecialValue[Zone]:
        return tuple(
            (
                self.lattice.top()
                if result.type.is_subseteq(grid.GridType)
                else self.lattice.bottom()
            )
            for result in stmt.results
        )

    def run_method(self, method: ir.Method, args: tuple[Zone, ...]):
        # NOTE: we do not support dynamic calls here, thus no need to propagate method object
        return self.run_callable(method.code, (self.lattice.bottom(),) + args)

from bloqade.geometry.dialects import grid
from kirin.analysis.forward import ForwardFrame
from kirin.interp import MethodTable, impl

from .. import analysis, lattice


@grid.dialect.register(key="zone.analysis")
class GridImpl(MethodTable):
    @impl(grid.GetSubGrid)
    def new_grid(
        self,
        interp: analysis.ZoneAnalysis,
        frame: ForwardFrame[lattice.Zone],
        stmt: grid.GetSubGrid,
    ):

        zone = frame.get(stmt.zone)

        if isinstance(zone, lattice.InvalidZone):
            return (lattice.InvalidZone(),)

        return (
            lattice.GetSubGridOfZone(
                zone=zone,
                x_indices=lattice.Zone.bottom(),
                y_indices=lattice.Zone.bottom(),
            ),
        )

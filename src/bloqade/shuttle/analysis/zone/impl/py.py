from bloqade.geometry.dialects.grid.types import Grid, SubGrid
from kirin.analysis.forward import ForwardFrame
from kirin.dialects import py
from kirin.interp import MethodTable, impl

from .. import analysis, lattice


@py.indexing.dialect.register(key="zone.analysis")
class GetIndexImpl(MethodTable):
    @impl(py.indexing.GetItem)
    def get_item(
        self,
        interp: analysis.ZoneAnalysis,
        frame: ForwardFrame[lattice.Zone],
        stmt: py.indexing.GetItem,
    ):
        obj = frame.get(stmt.obj)

        if isinstance(obj, lattice.InvalidZone):
            return (lattice.InvalidZone(),)

        if isinstance(obj, lattice.Zone):
            return (lattice.GetItemOfZone(obj, frame.get(stmt.index)),)

        return (lattice.NotZone(),)


@py.constant.dialect.register(key="zone.analysis")
class ConstantImpl(MethodTable):
    @impl(py.Constant)
    def constant(
        self,
        interp: analysis.ZoneAnalysis,
        frame: ForwardFrame[lattice.Zone],
        stmt: py.Constant,
    ):
        zone = stmt.value.unwrap()

        if isinstance(zone, SubGrid):
            # handle cases where ir has been folded
            zone_lattice = interp.get_grid_lattice(zone.parent)
            if isinstance(zone_lattice, lattice.InvalidZone):
                return (lattice.InvalidZone(),)

            return (
                lattice.GetSubGridOfZone(
                    zone=interp.get_grid_lattice(zone.parent),
                    x_indices=lattice.Zone.bottom(),
                    y_indices=lattice.Zone.bottom(),
                ),
            )
        elif isinstance(zone, Grid):
            return (interp.get_grid_lattice(zone),)

        return (lattice.NotZone(),)

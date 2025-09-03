from bloqade.geometry.dialects import grid
from kirin import ir
from kirin.dialects import func

from bloqade.shuttle import spec
from bloqade.shuttle.analysis import zone
from bloqade.shuttle.passes.hint_zone import HintZone
from bloqade.shuttle.prelude import move


def return_stmts(kernel: ir.Method) -> list[func.Return]:
    return [
        stmt for stmt in kernel.callable_region.walk() if isinstance(stmt, func.Return)
    ]


def default_spec():
    arch_spec = spec.ArchSpec(
        spec.Layout(
            static_traps={"test": grid.Grid.from_positions([0, 1, 2], [0, 1, 2])},
            fillable=set(["test"]),
            has_cz=set(["test"]),
            has_local=set(["test"]),
        )
    )

    return arch_spec


def test_zone_analysis_unfolded():

    arch_spec = default_spec()

    @move
    def kernel():
        zone = spec.get_static_trap(zone_id="test")
        return zone

    (return_stmt,) = return_stmts(kernel)
    HintZone(move, arch_spec)(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.SpecZone("test")


def test_zone_analysis_folded():
    arch_spec = default_spec()

    @move(arch_spec=arch_spec)
    def kernel():
        zone = spec.get_static_trap(zone_id="test")
        return zone

    (return_stmt,) = return_stmts(kernel)
    HintZone(move, arch_spec)(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.SpecZone("test")


def test_zone_analysis_invalid():
    arch_spec = default_spec()

    @move(arch_spec=arch_spec)
    def kernel():
        zone = spec.get_static_trap(zone_id="invalid")
        return zone

    (return_stmt,) = return_stmts(kernel)
    HintZone(move, arch_spec)(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.InvalidSpecId("invalid")


def test_zone_analysis_subgrid():
    arch_spec = default_spec()

    @move
    def kernel():
        zone = spec.get_static_trap(zone_id="test")
        subgrid = grid.sub_grid(zone, [0, 1], [0, 1])
        return subgrid

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.GetSubGridOfZone(
        zone=zone.SpecZone("test"),
        x_indices=zone.Zone.bottom(),
        y_indices=zone.Zone.bottom(),
    )


def test_zone_analysis_subgrid_folded():
    arch_spec = default_spec()

    @move(arch_spec=arch_spec)
    def kernel():
        zone = spec.get_static_trap(zone_id="test")
        subgrid = grid.sub_grid(zone, [0, 1], [0, 1])
        return subgrid

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.GetSubGridOfZone(
        zone=zone.SpecZone("test"),
        x_indices=zone.Zone.bottom(),
        y_indices=zone.Zone.bottom(),
    )


def test_zone_analysis_subgrid_invalid():
    arch_spec = default_spec()

    @move
    def kernel():
        zone = spec.get_static_trap(zone_id="invalid")
        subgrid = grid.sub_grid(zone, [0, 1], [0, 1])
        return subgrid

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.InvalidZone()


def test_zone_analysis_getitem():
    arch_spec = default_spec()

    @move
    def kernel():
        zone = spec.get_static_trap(zone_id="test")
        return zone[:2, 1:]  # type: ignore

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.GetItemOfZone(
        zone=zone.SpecZone("test"),
        index=zone.Zone.bottom(),
    )


def test_zone_analysis_getitem_invalid():
    arch_spec = default_spec()

    @move
    def kernel():
        zone = spec.get_static_trap(zone_id="invalid")
        return zone[:2, 1:]  # type: ignore

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.InvalidZone()


def test_zone_analysis_getitem_no_zone():
    arch_spec = default_spec()

    @move
    def kernel():
        a = [1, 2, 3]
        return a[:2]  # type: ignore

    HintZone(move, arch_spec)(kernel)
    (return_stmt,) = return_stmts(kernel)

    assert return_stmt.value.hints["zone.analysis"] == zone.NotZone()

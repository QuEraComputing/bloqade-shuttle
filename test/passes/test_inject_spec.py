from bloqade.geometry.dialects import grid

from bloqade.shuttle import spec
from bloqade.shuttle.passes import inject_spec
from bloqade.shuttle.prelude import move


def test_inject_spec():
    slm_grid = grid.Grid.from_positions([1, 2, 3], [4, 5, 6])
    test_spec = spec.ArchSpec(
        layout=spec.Layout({"slm": slm_grid}, fillable=set(["slm"]))
    )

    @move(arch_spec=test_spec)
    def test():
        return spec.get_static_trap(zone_id="slm")

    assert (
        test() == slm_grid
    ), "The injected static trap should match the expected grid."


def test_inject_spac_callgraph():

    slm_grid = grid.Grid.from_positions([1, 2, 3], [4, 5, 6])
    test_spec = spec.ArchSpec(
        layout=spec.Layout({"slm": slm_grid}, fillable=set(["slm"]))
    )

    @move
    def subroutine(depth: int):
        slm = spec.get_static_trap(zone_id="slm")

        if depth >= 1:

            def lambda_func():
                return slm

            return lambda_func

        return subroutine(depth + 1)

    @move
    def test():
        res = subroutine(0)
        return res()

    inject_spec.InjectSpecsPass(move, arch_spec=test_spec, fold=False)(test)

    test.verify_type()

    assert (
        test() == slm_grid
    ), "The injected static trap should match the expected grid."

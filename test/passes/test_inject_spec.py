from bloqade.geometry.dialects import grid

from bloqade.shuttle import spec
from bloqade.shuttle.prelude import move


def test_inject_spect():
    slm_grid = grid.Grid.from_positions([1, 2, 3], [4, 5, 6])
    test_spec = spec.Spec(layout=spec.Layout({"slm": slm_grid}, fillable=set(["slm"])))

    @move(arch_spec=test_spec)
    def test():
        return spec.get_static_trap(zone_id="slm")

    assert (
        test() == slm_grid
    ), "The injected static trap should match the expected grid."

from bloqade.geometry.dialects.grid import Grid

from bloqade.shuttle.arch import Layout


def test_layout():

    layout = Layout({"test": Grid.from_positions(range(16), range(16))}, {"test"})

    assert hash(layout) == hash(
        (frozenset(layout.static_traps.items()), frozenset(layout.fillable))
    )
    assert layout == Layout(
        {"test": Grid.from_positions(range(16), range(16))}, {"test"}
    )
    assert layout != 1

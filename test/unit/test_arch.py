from bloqade.geometry.dialects.grid import Grid

from bloqade.shuttle.arch import Layout


def test_layout():

    layout = Layout(
        {"test": Grid.from_positions(range(16), range(16))},
        {"test"},
        {"test"},
        {"test"},
    )

    assert hash(layout) == hash(
        (
            frozenset(layout.static_traps.items()),
            frozenset(layout.fillable),
            frozenset(layout.has_cz),
            frozenset(layout.has_local),
            frozenset(layout.special_grid.items()),
        )
    )
    assert layout == Layout(
        {"test": Grid.from_positions(range(16), range(16))},
        {"test"},
        {"test"},
        {"test"},
    )
    assert layout != 1

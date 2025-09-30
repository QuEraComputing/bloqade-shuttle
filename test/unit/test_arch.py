import pytest
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
    assert layout.bounding_box() == (0.0, 15.0, 0.0, 15.0)


def test_bounding_box_no_positions():
    layout = Layout(
        {"test": Grid.from_positions([], [])},
        {"test"},
        {"test"},
        {"test"},
    )

    with pytest.raises(ValueError):
        layout.bounding_box()

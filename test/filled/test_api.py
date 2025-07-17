from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import filled
from bloqade.shuttle.prelude import move


def test_vacat():

    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacat(zone, filling)

        shifted_zone = filled.shift(new_zone, 1, 1)
        scaled_zone = filled.scale(shifted_zone, 2, 2)

        return filled.repeat(scaled_zone, 2, 3, 10, 5)

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacat(
        parent,
        [(0, 0), (1, 1), (2, 2)],
    ).shift(
        1, 1
    ).scale(2, 2).repeat(2, 3, 10, 5)


def test_shift():
    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacat(zone, filling)

        shifted_zone = filled.shift(new_zone, 1, 1)
        return shifted_zone

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacat(
        parent.shift(1, 1),
        [(0, 0), (1, 1), (2, 2)],
    )


def test_scale():
    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacat(zone, filling)
        shifted_zone = filled.scale(new_zone, 1, 1)
        return shifted_zone

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacat(
        parent.scale(1, 1),
        [(0, 0), (1, 1), (2, 2)],
    )

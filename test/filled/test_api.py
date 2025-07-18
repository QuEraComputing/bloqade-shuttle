from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import filled
from bloqade.shuttle.prelude import move


def test_vacate():

    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacate(zone, filling)

        shifted_zone = filled.shift(new_zone, 1, 1)
        scaled_zone = filled.scale(shifted_zone, 2, 2)

        return filled.repeat(scaled_zone, 2, 3, 10, 5)

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacate(
        parent,
        frozenset([(0, 0), (1, 1), (2, 2)]),
    ).shift(1, 1).scale(2, 2).repeat(2, 3, 10, 5)


def test_shift():
    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacate(zone, filling)

        shifted_zone = filled.shift(new_zone, 1, 1)
        return shifted_zone

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacate(
        parent.shift(1, 1),
        frozenset([(0, 0), (1, 1), (2, 2)]),
    )


def test_scale():
    @move
    def test():
        zone = grid.from_positions([0, 1, 2], [0, 1, 2])
        filling = ilist.IList([(0, 0), (1, 1), (2, 2)])
        new_zone = filled.vacate(zone, filling)
        shifted_zone = filled.scale(new_zone, 1, 1)
        return shifted_zone

    parent = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])

    assert test() == filled.FilledGrid.vacate(
        parent.scale(1, 1),
        [(0, 0), (1, 1), (2, 2)],
    )


def test_positions():
    expected_positions = ilist.IList(((0.3, 0.88), (0.3, 0.99), (0.4, 0.99)))
    assert (
        filled.FilledGrid.vacate(
            grid.Grid.from_positions([0.3, 0.4], [0.88, 0.99]), frozenset([(1, 0)])
        ).positions
        == expected_positions
    )


def test_repeat():
    original = filled.FilledGrid.vacate(
        grid.Grid.from_positions([0.3, 0.4], [0.88, 0.99]), frozenset([(0, 1)])
    )

    tiled = original.repeat(2, 3, 10, 5)
    parent = original.parent.repeat(2, 3, 10, 5)

    expected_vacancies = frozenset(
        [
            (0, 1),
            (0, 3),
            (0, 5),
            (2, 1),
            (2, 3),
            (2, 5),
        ]
    )

    assert tiled.parent == parent
    assert tiled.vacancies == expected_vacancies


def test_fill_filled():

    zone = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])
    filled_1 = filled.FilledGrid.fill(zone, [(0, 0)])
    assert filled_1.vacancies == frozenset(
        [(1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)]
    )

    filled_2 = filled.FilledGrid.fill(filled_1, [(1, 1), (1, 2)])
    assert filled_2.vacancies == frozenset(
        [(1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]
    )


def test_fill_vacated():
    zone = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])
    filled_1 = filled.FilledGrid.vacate(zone, [(0, 0), (0, 1), (0, 2)])
    assert filled_1.vacancies == frozenset([(0, 0), (0, 1), (0, 2)])

    filled_2 = filled.FilledGrid.fill(filled_1, [(1, 1), (1, 2)])
    assert filled_1.vacancies == frozenset([(0, 0), (0, 1), (0, 2)])

    filled_3 = filled.FilledGrid.fill(filled_2, [(0, 0)])
    assert filled_3.vacancies == frozenset([(0, 1), (0, 2)])


def test_vacate_filled():
    zone = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])
    filled_1 = filled.FilledGrid.fill(zone, [(0, 0), (0, 1), (0, 2)])
    assert filled_1.vacancies == frozenset(
        [(1, 0), (2, 0), (1, 1), (2, 1), (1, 2), (2, 2)]
    )

    filled_2 = filled.FilledGrid.vacate(filled_1, [(1, 1), (1, 2)])
    assert filled_2.vacancies == frozenset(
        [(1, 0), (2, 0), (1, 1), (2, 1), (1, 2), (2, 2)]
    )

    filled_3 = filled.FilledGrid.vacate(filled_2, [(0, 1)])
    assert filled_3.vacancies == frozenset(
        [(1, 0), (2, 0), (1, 1), (2, 1), (1, 2), (2, 2), (0, 1)]
    )


def test_get_view():
    zone = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])
    filled_1 = filled.FilledGrid.vacate(zone, [(0, 0), (0, 1), (0, 2)])

    view = filled_1.get_view(ilist.IList([0, 2]), ilist.IList([0, 2]))

    assert view.vacancies == frozenset([(0, 0), (0, 1)])

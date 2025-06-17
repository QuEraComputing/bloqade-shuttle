from bloqade.geometry.dialects import grid

from bloqade.shuttle.dialects import action
from bloqade.shuttle.prelude import tweezer


def test_move():

    @tweezer
    def k1(a: float, b: float, c: float, d: float, e: float):
        start = grid.from_positions([a, b], [c, d, e])
        end = grid.from_positions([a, b + 4], [c, d, e])

        action.turn_on(action.ALL, action.ALL)
        action.set_loc(start)
        action.move(end)
        action.turn_off(action.ALL, action.ALL)

    assert isinstance(k1.code, action.TweezerFunction)

from bloqade.geometry.dialects import grid

from bloqade.shuttle.arch import ArchSpec
from bloqade.shuttle.codegen.taskgen import (
    TraceInterpreter,
    TurnOffXYSliceAction,
    TurnOnXYSliceAction,
    WayPointsAction,
)
from bloqade.shuttle.dialects import action
from bloqade.shuttle.prelude import tweezer


def test_trace():

    @tweezer
    def move_fn(x: float, y: float):
        start = grid.from_positions([x], [y])
        end = grid.from_positions([x + 1], [y + 1])

        action.set_loc(start)
        action.turn_on(slice(None), slice(None))
        action.move(end)
        action.turn_off(slice(None), slice(None))

    move_fn.print()

    action_list = TraceInterpreter(ArchSpec()).run_trace(move_fn, (1.0, 2.0), {})

    assert isinstance(action_list, list)

    assert isinstance(action_list[0], WayPointsAction)
    assert isinstance(action_list[1], TurnOnXYSliceAction)
    assert isinstance(action_list[2], WayPointsAction)
    assert isinstance(action_list[3], TurnOffXYSliceAction)
    assert isinstance(action_list[4], WayPointsAction)

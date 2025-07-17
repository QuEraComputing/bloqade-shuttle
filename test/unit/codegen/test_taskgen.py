import pytest
from bloqade.geometry.dialects import grid
from kirin import interp, ir, prelude
from kirin.dialects import ilist

from bloqade.shuttle.arch import ArchSpec
from bloqade.shuttle.codegen import taskgen
from bloqade.shuttle.dialects import action
from bloqade.shuttle.prelude import tweezer


class TestWaypointsAction:

    def get_waypoint_action(self):
        return taskgen.WayPointsAction()

    def test_init(self):
        waypoint_action = self.get_waypoint_action()
        assert waypoint_action.way_points == []

    def test_add_waypoint(self):
        waypoint_action = self.get_waypoint_action()
        waypoint_action.add_waypoint(pos := grid.Grid.from_positions([1, 2], [3, 4, 5]))
        assert waypoint_action.way_points == [pos]

    def test_inv(self):
        waypoint_action = self.get_waypoint_action()
        waypoint_action.add_waypoint(
            pos1 := grid.Grid.from_positions([1, 2], [3, 4, 5])
        )
        waypoint_action.add_waypoint(
            pos2 := grid.Grid.from_positions([6, 7], [8, 9, 10])
        )
        inverted = waypoint_action.inv()
        assert inverted.way_points == [pos2, pos1]

    def test_repr(self):
        waypoint_action = self.get_waypoint_action()
        waypoint_action.add_waypoint(grid.Grid.from_positions([1, 2], [3, 4, 5]))
        assert (
            repr(waypoint_action) == f"WayPointsAction({waypoint_action.way_points!r})"
        )


class TestTurnOnAction:
    def get_turn_on_action(self):
        return taskgen.TurnOnXYAction(ilist.IList([1, 2]), ilist.IList([3, 4]))

    def test_init(self):
        turn_on_action = self.get_turn_on_action()
        assert turn_on_action.x_tone_indices == ilist.IList([1, 2])
        assert turn_on_action.y_tone_indices == ilist.IList([3, 4])

    def test_inv(self):
        turn_on_action = self.get_turn_on_action()
        inverted = turn_on_action.inv()
        assert isinstance(inverted, taskgen.TurnOffXYAction)
        assert inverted.x_tone_indices == ilist.IList([1, 2])
        assert inverted.y_tone_indices == ilist.IList([3, 4])


class TestTurnOffAction:
    def get_turn_off_action(self):
        return taskgen.TurnOffXYAction(ilist.IList([1, 2]), ilist.IList([3, 4]))

    def test_init(self):
        turn_off_action = self.get_turn_off_action()
        assert turn_off_action.x_tone_indices == ilist.IList([1, 2])
        assert turn_off_action.y_tone_indices == ilist.IList([3, 4])

    def test_inv(self):
        turn_off_action = self.get_turn_off_action()
        inverted = turn_off_action.inv()
        assert isinstance(inverted, taskgen.TurnOnXYAction)
        assert inverted.x_tone_indices == ilist.IList([1, 2])
        assert inverted.y_tone_indices == ilist.IList([3, 4])


class TestActionMethods:

    @property
    def start_pos(self):
        return grid.Grid.from_positions([1, 2], [3, 4])

    def init_interpreter(self):
        interpreter = taskgen.TraceInterpreter(ArchSpec())
        interpreter.initialize()
        return interpreter

    def init_with_current_pos(self):
        interpreter = self.init_interpreter()
        interpreter.curr_pos = self.start_pos
        interpreter.trace = [taskgen.WayPointsAction([self.start_pos])]
        return interpreter

    def test_move_error(self):
        pos_ssa = ir.TestValue()
        pos = grid.Grid.from_positions([4, 5], [3, 4])
        interpreter = self.init_interpreter()

        with pytest.raises(interp.InterpreterError):
            interpreter.run_stmt(action.Move(pos_ssa), (pos,))

    def test_move(self):
        pos_ssa = ir.TestValue()
        pos = grid.Grid.from_positions([4, 5], [3, 4])
        interpreter = self.init_with_current_pos()
        interpreter.run_stmt(action.Move(pos_ssa), (pos,))

        assert interpreter.trace == [
            taskgen.WayPointsAction([self.start_pos, pos]),
        ]

    def test_set(self):
        pos_ssa = ir.TestValue()
        pos = grid.Grid.from_positions([4, 5], [3, 4])
        interpreter = self.init_interpreter()
        interpreter.run_stmt(action.Set(pos_ssa), (pos,))

        assert interpreter.trace == [
            taskgen.WayPointsAction([pos]),
        ]

    def test_turn_on_error(self):
        x_slice_ssa = ir.TestValue()
        y_slice_ssa = ir.TestValue()
        x_tone_indices = ilist.IList([1, 2])
        y_tone_indices = ilist.IList([3, 4])

        interpreter = self.init_interpreter()

        with pytest.raises(interp.InterpreterError):
            interpreter.run_stmt(
                action.TurnOn(x_slice_ssa, y_slice_ssa),
                (x_tone_indices, y_tone_indices),
            )

    def test_turn_off_error(self):
        x_slice_ssa = ir.TestValue()
        y_slice_ssa = ir.TestValue()
        x_tone_indices = ilist.IList([1, 2])
        y_tone_indices = ilist.IList([3, 4])

        interpreter = self.init_interpreter()

        with pytest.raises(interp.InterpreterError):
            interpreter.run_stmt(
                action.TurnOff(x_slice_ssa, y_slice_ssa),
                (x_tone_indices, y_tone_indices),
            )

    @pytest.mark.parametrize(
        ["StmtType", "ActionType", "x_tone_indices", "y_tone_indices"],
        [
            (
                action.TurnOnXYSlice,
                taskgen.TurnOnXYSliceAction,
                slice(1, 2),
                slice(3, 4),
            ),
            (action.TurnOnXSlice, taskgen.TurnOnXSliceAction, slice(1, 2), [1, 2]),
            (
                action.TurnOnYSlice,
                taskgen.TurnOnYSliceAction,
                ilist.IList([1, 2]),
                slice(3, 4),
            ),
            (
                action.TurnOnXY,
                taskgen.TurnOnXYAction,
                ilist.IList([1, 2]),
                ilist.IList([3, 4]),
            ),
            (
                action.TurnOffXYSlice,
                taskgen.TurnOffXYSliceAction,
                slice(1, 2),
                slice(3, 4),
            ),
            (action.TurnOffXSlice, taskgen.TurnOffXSliceAction, slice(1, 2), [1, 2]),
            (
                action.TurnOffYSlice,
                taskgen.TurnOffYSliceAction,
                ilist.IList([1, 2]),
                slice(3, 4),
            ),
            (
                action.TurnOffXY,
                taskgen.TurnOffXYAction,
                ilist.IList([1, 2]),
                ilist.IList([3, 4]),
            ),
        ],
    )
    def test_intensity_actions(
        self, StmtType, ActionType, x_tone_indices, y_tone_indices
    ):
        x_slice_ssa = ir.TestValue()
        y_slice_ssa = ir.TestValue()

        interpreter = self.init_with_current_pos()
        interpreter.run_stmt(
            StmtType(x_slice_ssa, y_slice_ssa),
            (x_tone_indices, y_tone_indices),
        )

        assert interpreter.trace == [
            taskgen.WayPointsAction([self.start_pos]),
            ActionType(x_tone_indices, y_tone_indices),
            taskgen.WayPointsAction([self.start_pos]),
        ]


def test_reverse_path():
    path: list[taskgen.AbstractAction] = [
        taskgen.WayPointsAction([grid.Grid.from_positions([1, 2], [3, 4])]),
        taskgen.TurnOnXYAction(ilist.IList([1, 2]), ilist.IList([3, 4])),
        taskgen.WayPointsAction([grid.Grid.from_positions([5, 6], [7, 8])]),
        taskgen.TurnOffXYAction(ilist.IList([1, 2]), ilist.IList([3, 4])),
    ]

    assert taskgen.reverse_path(path) == [act.inv() for act in reversed(path)]


def test_interpreter_trace():

    @tweezer
    def test_action(self):
        action.set_loc(grid.from_positions([1.0, 2.0], [3.0, 4.0]))
        action.turn_on(action.ALL, action.ALL)
        action.turn_off(action.ALL, action.ALL)

    interpreter = taskgen.TraceInterpreter(ArchSpec())
    assert interpreter.run_trace(test_action, (), {}) == [
        taskgen.WayPointsAction([grid.Grid.from_positions([1, 2], [3, 4])]),
        taskgen.TurnOnXYSliceAction(action.ALL, action.ALL),
        taskgen.WayPointsAction([grid.Grid.from_positions([1, 2], [3, 4])]),
        taskgen.TurnOffXYSliceAction(action.ALL, action.ALL),
        taskgen.WayPointsAction([grid.Grid.from_positions([1, 2], [3, 4])]),
    ]


def test_interpreter_run_trace_error():
    @prelude.basic_no_opt
    def test_bad_method():
        return None

    interpreter = taskgen.TraceInterpreter(ArchSpec())

    with pytest.raises(ValueError):
        interpreter.run_trace(test_bad_method, (), {})

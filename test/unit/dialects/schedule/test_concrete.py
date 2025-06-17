import pytest
from kirin import interp, ir
from kirin.dialects import ilist

from bloqade.shuttle.dialects import action, schedule
from bloqade.shuttle.prelude import move, tweezer


@tweezer
def test_move():
    action.turn_on(action.ALL, action.ALL)
    action.turn_off(action.ALL, action.ALL)


class TestScheduleInterpreter:

    def init_interpreter(self):
        interpreter = interp.Interpreter(move)
        interpreter.initialize()

        return interpreter

    def run_stmt(self, stmt_type: type[ir.Statement], *values):
        interpreter = self.init_interpreter()
        ssa_values = tuple(ir.TestValue() for _ in values)
        new_stmt = stmt_type(*ssa_values)
        return interpreter.run_stmt(new_stmt, values)

    def test_new_device_function(self):

        x_tones = ilist.IList([1, 2, 3])
        y_tones = ilist.IList([4, 5, 6])

        result = self.run_stmt(
            schedule.NewDeviceFunction,
            test_move,
            x_tones,
            y_tones,
        )

        assert result == (
            schedule.DeviceFunction(
                move_fn=test_move, x_tones=x_tones, y_tones=y_tones
            ),
        )

    def test_reverse(self):
        x_tones = ilist.IList([1, 2, 3])
        y_tones = ilist.IList([4, 5, 6])

        device_task = schedule.DeviceFunction(
            move_fn=test_move,
            x_tones=x_tones,
            y_tones=y_tones,
        )
        reversed_task = schedule.ReverseDeviceFunction(device_task=device_task)

        result = self.run_stmt(schedule.Reverse, device_task)
        assert result == (reversed_task,)

        result = self.run_stmt(schedule.Reverse, reversed_task)
        assert result == (device_task,)

        with pytest.raises(interp.InterpreterError):
            self.run_stmt(schedule.Reverse, "invalid_task")

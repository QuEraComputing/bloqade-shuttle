from kirin import ir
from kirin.interp import Frame, Interpreter, InterpreterError, MethodTable, impl

from bloqade.shuttle.dialects.schedule import stmts, types
from bloqade.shuttle.dialects.schedule._dialect import dialect


@dialect.register
class ScheduleInterpreter(MethodTable):

    @impl(stmts.NewDeviceFunction)
    def device_fn(
        self, interp: Interpreter, frame: Frame, stmt: stmts.NewDeviceFunction
    ):
        move_fn: ir.Method = frame.get(stmt.move_fn)
        x_tones = frame.get(stmt.x_tones)
        y_tones = frame.get(stmt.y_tones)
        return (
            types.DeviceFunction(move_fn=move_fn, x_tones=x_tones, y_tones=y_tones),
        )

    @impl(stmts.Reverse)
    def reverse(self, interp: Interpreter, frame: Frame, stmt: stmts.Reverse):
        device_fn = frame.get(stmt.device_fn)
        if isinstance(device_fn, types.DeviceFunction):
            return (types.ReverseDeviceFunction(device_task=device_fn),)
        elif isinstance(device_fn, types.ReverseDeviceFunction):
            return (device_fn.device_task,)
        else:
            raise InterpreterError("Invalid device task type")

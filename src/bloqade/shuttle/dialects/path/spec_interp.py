from kirin.interp import (
    Frame,
    InterpreterError,
    MethodTable,
    impl,
)

from bloqade.shuttle.arch import ArchSpecInterpreter
from bloqade.shuttle.codegen import TraceInterpreter, reverse_path
from bloqade.shuttle.dialects import schedule
from bloqade.shuttle.dialects.path import dialect, stmts, types


@dialect.register(key="spec.interp")
class SpecPathInterpreter(MethodTable):

    @impl(stmts.Gen)
    def gen(self, interp: ArchSpecInterpreter, frame: Frame, stmt: stmts.Gen):

        device_task = frame.get(stmt.device_task)
        if isinstance(device_task, schedule.DeviceFunction):
            reverse = False
        elif isinstance(device_task, schedule.ReverseDeviceFunction):
            device_task = device_task.device_task
            reverse = True
        else:
            raise InterpreterError("Invalid device task type")

        inputs = frame.get_values(stmt.inputs)
        kwargs = stmt.kwargs
        args = interp.permute_values(device_task.move_fn.arg_names, inputs, kwargs)
        path = TraceInterpreter(interp.arch_spec).run_trace(
            device_task.move_fn, args, {}
        )

        if reverse:
            path = reverse_path(path)

        return (
            types.Path(
                x_tones=device_task.x_tones,
                y_tones=device_task.y_tones,
                path=path,
            ),
        )

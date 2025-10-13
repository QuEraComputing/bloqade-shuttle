from kirin.dialects import ilist
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

    @impl(stmts.AutoGen)
    def autogen(self, interp: ArchSpecInterpreter, frame: Frame, stmt: stmts.AutoGen):
        inputs = frame.get_values(stmt.inputs)
        kwargs = stmt.kwargs
        args = interp.permute_values(stmt.task.arg_names, inputs, kwargs)
        tr = TraceInterpreter(interp.arch_spec)
        path = tr.run_trace(stmt.task, args, {})

        if (curr_pos := tr.curr_pos) is None:
            raise InterpreterError("No positions generated in path.")

        num_x_tones, num_y_tones = curr_pos.shape

        return (
            types.Path(
                x_tones=ilist.IList(range(num_x_tones)),
                y_tones=ilist.IList(range(num_y_tones)),
                path=path,
            ),
        )

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

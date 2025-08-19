from typing import cast

from kirin.analysis import const, forward
from kirin.interp import MethodTable, impl

from bloqade.shuttle.codegen import TraceInterpreter, reverse_path
from bloqade.shuttle.dialects import schedule
from bloqade.shuttle.dialects.path import dialect, stmts, types


@dialect.register(key="constprop")
class ConstProp(MethodTable):

    @impl(stmts.Gen)
    def gen(
        self,
        interp: const.Propagate,
        frame: forward.ForwardFrame[const.Result],
        stmt: stmts.Gen,
    ):
        if stmt.arch_spec is None:
            return (const.Result.top(),)

        device_task_prop = frame.get(stmt.device_task)
        if not isinstance(device_task_prop, const.Value):
            return (const.Result.top(),)

        if isinstance(device_task := device_task_prop.data, schedule.DeviceFunction):
            reverse = False
        elif isinstance(device_task, schedule.ReverseDeviceFunction):
            device_task = device_task.device_task
            reverse = True
        else:
            return (const.Result.top(),)

        inputs_results = frame.get_values(stmt.inputs)

        if not all(isinstance(input_, const.Value) for input_ in inputs_results):
            return (const.Result.top(),)

        kwargs = stmt.kwargs
        args = interp.permute_values(
            device_task.move_fn.arg_names, inputs_results, kwargs
        )

        path = TraceInterpreter(stmt.arch_spec).run_trace(
            device_task.move_fn,
            tuple(
                cast(const.Value, arg).data if isinstance(arg, const.Value) else arg
                for arg in args
            ),
            {},
        )

        if reverse:
            path = reverse_path(path)

        return (
            const.Value(
                types.Path(
                    x_tones=device_task.x_tones,
                    y_tones=device_task.y_tones,
                    path=path,
                )
            ),
        )

from kirin import ir
from kirin.analysis.forward import ForwardFrame
from kirin.interp import MethodTable, impl

from bloqade.shuttle.analysis import schedule

from .. import stmts
from .._dialect import dialect


@dialect.register(key="path.schedule")
class ScheduleInterpreter(MethodTable):

    @impl(stmts.NewTweezerTask)
    def tweezer_task(
        self,
        interp: schedule.SchedulerAnalysis,
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.NewTweezerTask,
    ):
        move_fn = interp.get_const_value(ir.Method, stmt.move_fn)
        if move_fn is None:
            return (schedule.ScheduleLattice.top(),)

        return (schedule.TweezerTask(move_fn=move_fn),)

    @impl(stmts.NewDeviceFunction)
    def device_fn(
        self,
        interp: schedule.SchedulerAnalysis,
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.NewDeviceFunction,
    ):
        x_tones = interp.get_const_value(tuple[int, ...], stmt.x_tones)
        y_tones = interp.get_const_value(tuple[int, ...], stmt.y_tones)
        move_fn = interp.get_const_value(ir.Method, stmt.move_fn)

        if x_tones is None or y_tones is None or move_fn is None:
            return (schedule.ScheduleLattice.top(),)

        return (
            schedule.DeviceFunction(move_fn=move_fn, x_tones=x_tones, y_tones=y_tones),
        )

    @impl(stmts.Reverse)
    def reverse(
        self,
        interp: schedule.SchedulerAnalysis,
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.Reverse,
    ):
        fn = frame.get(stmt.device_fn)
        if isinstance(fn, schedule.Reverse):
            return (fn.task_or_fn,)
        else:
            return (schedule.Reverse(task_or_fn=fn),)

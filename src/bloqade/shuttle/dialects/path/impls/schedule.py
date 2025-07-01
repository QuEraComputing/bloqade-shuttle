from typing import Any, TypeVar

from kirin.analysis import const
from kirin.analysis.forward import ForwardFrame
from kirin.interp import MethodTable, impl

from ....analysis import schedule
from ....codegen import TraceInterpreter, reverse_path
from .. import stmts
from .._dialect import dialect


@dialect.register(key="path.schedule")
class ScheduleInterpreter(MethodTable):
    @impl(stmts.Gen)
    def gen(
        self,
        interp: schedule.SchedulerAnalysis,
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.Gen,
    ):
        task = frame.get(stmt.task)
        if isinstance(task, schedule.NoSchedule):
            return (task,)

        reverse = False
        if isinstance(task, schedule.Reverse):
            reverse = True
            task = task.task_or_fn

        x_tones = None
        y_tones = None
        if isinstance(task, schedule.DeviceFunction):
            move_fn = task.move_fn
            x_tones = task.x_tones
            y_tones = task.y_tones
        elif isinstance(task, schedule.TweezerTask):
            move_fn = task.move_fn
        else:
            return (schedule.ScheduleLattice.top(),)

        inputs: list[Any] = []

        for input_ in stmt.inputs:
            const_prop = input_.hints.get("const")
            if isinstance(const_prop, const.Value):
                inputs.append(const_prop.data)
            else:
                return (schedule.ScheduleLattice.top(),)

        kwargs = stmt.kwargs
        args = interp.permute_values(move_fn.arg_names, tuple(inputs), kwargs)
        actions = TraceInterpreter(move_fn.dialects).run_trace(move_fn, args, {})

        if reverse:
            actions = reverse_path(actions)

        if x_tones is None or y_tones is None:
            return (schedule.NeedsTones(actions=tuple(actions)),)
        return (
            schedule.ConcretePath(
                x_tones=x_tones,
                y_tones=y_tones,
                actions=tuple(actions),
            ),
        )

    @impl(stmts.Parallel)
    def parallel(
        self,
        interp: schedule.SchedulerAnalysis,
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.Parallel,
    ):
        paths = []
        for task in stmt.paths:
            task_lattice = frame.get(task)
            if isinstance(task_lattice, schedule.NoSchedule):
                return (task_lattice,)
            paths.append(task_lattice)

        return (schedule.ParallelSchedule(paths=tuple(paths)),)

    Scheduler = TypeVar("Scheduler", bound=schedule.SchedulerABC, covariant=True)

    @impl(stmts.Auto)
    def auto(
        self,
        interp: schedule.SchedulerAnalysis[Scheduler],
        frame: ForwardFrame[schedule.ScheduleLattice],
        stmt: stmts.Auto,
    ):
        paths: list[schedule.PathLike] = []
        for task in stmt.paths:
            task_lattice = frame.get(task)
            if not isinstance(task_lattice, schedule.PathLike):
                return (task_lattice,)
            paths.append(task_lattice)

        return (interp.scheduler.schedule(paths),)

import abc
from dataclasses import dataclass, field
from functools import cache
from typing import Any, ClassVar, Dict, Optional

from bloqade.geometry.dialects import grid
from kirin import ir
from kirin.dialects import func, ilist
from kirin.interp import Frame, InterpreterError, MethodTable, impl
from kirin.ir.method import Method
from typing_extensions import Self

from bloqade.shuttle.arch import ArchSpecInterpreter
from bloqade.shuttle.dialects import action


class AbstractAction(abc.ABC):
    @abc.abstractmethod
    def inv(self) -> "AbstractAction": ...


@dataclass
class WayPointsAction(AbstractAction):
    way_points: list[grid.Grid] = field(default_factory=list)

    def add_waypoint(self, pos: grid.Grid):
        self.way_points.append(pos)

    def inv(self):
        return WayPointsAction(list(reversed(self.way_points)))

    def __repr__(self):
        return f"WayPointsAction({self.way_points!r})"


@dataclass(frozen=True)
class TurnOnAction(AbstractAction):
    x_tone_indices: Any
    y_tone_indices: Any


@dataclass(frozen=True)
class TurnOffAction(AbstractAction):
    x_tone_indices: Any
    y_tone_indices: Any


@dataclass(frozen=True)
class TurnOnXYAction(TurnOnAction):
    x_tone_indices: ilist.IList[int, Any]
    y_tone_indices: ilist.IList[int, Any]

    def inv(self):
        return TurnOffXYAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOffXYAction(TurnOffAction):
    x_tone_indices: ilist.IList[int, Any]
    y_tone_indices: ilist.IList[int, Any]

    def inv(self):
        return TurnOnXYAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOnXSliceAction(TurnOnAction):
    x_tone_indices: slice
    y_tone_indices: ilist.IList[int, Any]

    def inv(self):
        return TurnOffXSliceAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOffXSliceAction(TurnOffAction):
    x_tone_indices: slice
    y_tone_indices: ilist.IList[int, Any]

    def inv(self):
        return TurnOnXSliceAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOnYSliceAction(TurnOnAction):
    x_tone_indices: ilist.IList[int, Any]
    y_tone_indices: slice

    def inv(self):
        return TurnOffYSliceAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOffYSliceAction(TurnOffAction):
    x_tone_indices: ilist.IList[int, Any]
    y_tone_indices: slice

    def inv(self):
        return TurnOnYSliceAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOnXYSliceAction(TurnOnAction):
    x_tone_indices: slice
    y_tone_indices: slice

    def inv(self):
        return TurnOffXYSliceAction(self.x_tone_indices, self.y_tone_indices)


@dataclass(frozen=True)
class TurnOffXYSliceAction(TurnOffAction):
    x_tone_indices: slice
    y_tone_indices: slice

    def inv(self):
        return TurnOnXYSliceAction(self.x_tone_indices, self.y_tone_indices)


def reverse_path(path: list[AbstractAction]) -> list[AbstractAction]:
    return [action.inv() for action in reversed(path)]


@cache
def _default_dialect():
    from bloqade.shuttle.prelude import (
        tweezer,  # needs to be here to avoid circular import issues
    )

    return tweezer


@dataclass
class TraceInterpreter(ArchSpecInterpreter):
    keys: ClassVar[list[str]] = ["action.tracer", "spec.interp", "main"]
    trace: list[AbstractAction] = field(init=False, default_factory=list)
    curr_pos: Optional[grid.Grid] = field(init=False, default=None)
    dialects: ir.DialectGroup = field(init=False, default_factory=_default_dialect)

    def initialize(self) -> Self:
        self.curr_pos = None
        self.trace = []
        return super().initialize()

    def run_trace(
        self, mt: Method, args: tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> list[AbstractAction]:

        if not isinstance(mt.code, (action.TweezerFunction, func.Lambda)):
            raise ValueError("Method code must be a MoveFunction or Lambda")

        # TODO: use permute_values to get correct order.
        super().run(mt, args=args, kwargs=kwargs)
        return self.trace.copy()


@action.dialect.register(key="action.tracer")
class ActionTracer(MethodTable):

    intensity_actions = {
        action.TurnOnXY: TurnOnXYAction,
        action.TurnOffXY: TurnOffXYAction,
        action.TurnOnXSlice: TurnOnXSliceAction,
        action.TurnOffXSlice: TurnOffXSliceAction,
        action.TurnOnYSlice: TurnOnYSliceAction,
        action.TurnOffYSlice: TurnOffYSliceAction,
        action.TurnOnXYSlice: TurnOnXYSliceAction,
        action.TurnOffXYSlice: TurnOffXYSliceAction,
    }

    @impl(action.TurnOnXY)
    @impl(action.TurnOffXY)
    @impl(action.TurnOnXSlice)
    @impl(action.TurnOffXSlice)
    @impl(action.TurnOnYSlice)
    @impl(action.TurnOffYSlice)
    @impl(action.TurnOnXYSlice)
    @impl(action.TurnOffXYSlice)
    def construct_intensity_actions(
        self,
        interp: TraceInterpreter,
        frame: Frame,
        stmt: action.IntensityStatement,
    ):
        if interp.curr_pos is None:
            raise InterpreterError(
                "Position of AOD not set before turning on/off tones"
            )

        x_tone_indices = frame.get(stmt.x_tones)
        y_tone_indices = frame.get(stmt.y_tones)

        interp.trace.append(
            self.intensity_actions[type(stmt)](
                x_tone_indices if isinstance(x_tone_indices, slice) else x_tone_indices,
                y_tone_indices if isinstance(y_tone_indices, slice) else y_tone_indices,
            )
        )
        interp.trace.append(WayPointsAction(way_points=[interp.curr_pos]))
        return ()

    @impl(action.Move)
    def move(self, interp: TraceInterpreter, frame: Frame, stmt: action.Move):
        if interp.curr_pos is None:
            raise InterpreterError("Position of AOD not set before moving tones")

        assert isinstance(interp.trace[-1], WayPointsAction)

        interp.trace[-1].add_waypoint(pos := frame.get_typed(stmt.grid, grid.Grid))
        if interp.curr_pos.shape != pos.shape:
            raise InterpreterError(
                f"Position of AOD {interp.curr_pos} and target position {pos} have different shapes"
            )
        interp.curr_pos = pos

        return ()

    @impl(action.Set)
    def set(self, interp: TraceInterpreter, frame: Frame, stmt: action.Set):
        pos = frame.get_typed(stmt.grid, grid.Grid)
        interp.trace.append(WayPointsAction([pos]))

        interp.curr_pos = pos

        return ()

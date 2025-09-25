import abc
from dataclasses import dataclass, field
from functools import cache
from typing import Any, ClassVar, Dict, Optional

from bloqade.geometry.dialects import grid
from kirin import ir
from kirin.dialects import func, ilist
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

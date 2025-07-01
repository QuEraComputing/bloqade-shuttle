import abc
from dataclasses import dataclass, field
from typing import Generic, Sequence, Type, TypeVar, Union

from kirin import ir
from kirin.analysis import const
from kirin.analysis.forward import Forward

from . import lattice

PathLike = Union[
    lattice.ConcretePath,
    lattice.NeedsTones,
    lattice.ParallelSchedule,
    lattice.AutoSchedule,
]


class SchedulerABC(abc.ABC):

    @abc.abstractmethod
    def schedule(self, paths: Sequence[PathLike]) -> lattice.AutoSchedule:
        """
        Schedule the given AutoSchedule and return a list of ParallelSchedules.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class SequentialScheduler(SchedulerABC):
    """
    A simple scheduler that processes Auto sequentially.
    """

    def schedule(self, paths: Sequence[PathLike]) -> lattice.AutoSchedule:
        """
        Schedule the given Auto by creating a ParallelSchedule for each group.
        """
        raise NotImplementedError("SequentialScheduler is not implemented yet.")


Scheduler = TypeVar("Scheduler", bound=SchedulerABC, covariant=True)


@dataclass
class SchedulerAnalysis(Forward[lattice.ScheduleLattice], Generic[Scheduler]):
    keys = ["path.schedule"]
    lattice = lattice.ScheduleLattice

    scheduler: Scheduler = field(default_factory=SequentialScheduler)  # type: ignore

    T = TypeVar("T")

    def get_const_value(self, type_: Type[T], ssa_value: ir.SSAValue) -> T | None:
        return (
            const_prop.data
            if isinstance(const_prop := ssa_value.hints.get("const"), const.Value)
            else None
        )

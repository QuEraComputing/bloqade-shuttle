from dataclasses import dataclass
from typing import final

from kirin import ir
from kirin.ir.attrs.abc import LatticeAttributeMeta
from kirin.lattice.abc import BoundedLattice
from kirin.lattice.mixin import SimpleJoinMixin, SimpleMeetMixin
from kirin.print.printer import Printer

from bloqade.shuttle.codegen.taskgen import AbstractAction
from bloqade.shuttle.dialects import path


@dataclass
class ScheduleLattice(
    ir.Attribute,
    SimpleJoinMixin["ScheduleLattice"],
    SimpleMeetMixin["ScheduleLattice"],
    BoundedLattice["ScheduleLattice"],
    metaclass=LatticeAttributeMeta,
):

    @classmethod
    def bottom(cls) -> "ScheduleLattice":
        return NoPath()

    @classmethod
    def top(cls) -> "ScheduleLattice":
        return NoSchedule()

    def print_impl(self, printer: Printer) -> None:
        printer.print(self.__class__.__name__ + "()")


@final
@dataclass
class NoPath(ScheduleLattice):

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return True


@final
@dataclass
class NoSchedule(ScheduleLattice):

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return isinstance(other, NoSchedule)


@dataclass
class ConcretePath(ScheduleLattice):
    path: path.Path

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return isinstance(other, ConcretePath) and self.path == other.path


@dataclass
class NeedsTones(ScheduleLattice):
    actions: tuple[AbstractAction, ...]

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return isinstance(other, NeedsTones) and self.actions == other.actions


@dataclass
class ParallelSchedule(ScheduleLattice):
    paths: tuple[ScheduleLattice, ...]

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return isinstance(other, ParallelSchedule) and all(
            p1.is_subseteq(p2) for p1, p2 in zip(self.paths, other.paths)
        )


@dataclass
class AutoSchedule(ScheduleLattice):
    @dataclass(frozen=True)
    class ToneData:
        x_tones: tuple[int, ...]
        y_tones: tuple[int, ...]

    paths: tuple[ScheduleLattice, ...]
    group_id: tuple[int, ...]
    tones: tuple[ToneData, ...]

    def is_subseteq(self, other: ScheduleLattice) -> bool:
        return (
            isinstance(other, AutoSchedule)
            and all(p1.is_subseteq(p2) for p1, p2 in zip(self.paths, other.paths))
            and self.group_id == other.group_id
            and self.tones == other.tones
        )

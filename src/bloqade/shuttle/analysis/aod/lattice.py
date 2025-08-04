from dataclasses import dataclass

from bloqade.geometry.dialects import grid
from kirin import ir
from kirin.dialects import ilist
from kirin.ir.attrs.abc import LatticeAttributeMeta
from kirin.lattice.abc import BoundedLattice
from kirin.lattice.mixin import SimpleJoinMixin, SimpleMeetMixin
from kirin.print.printer import Printer


@dataclass
class AODState(
    ir.Attribute,
    SimpleJoinMixin["AODState"],
    SimpleMeetMixin["AODState"],
    BoundedLattice["AODState"],
    metaclass=LatticeAttributeMeta,
):

    @classmethod
    def bottom(cls) -> "AODState":
        return NotAOD()

    @classmethod
    def top(cls) -> "AODState":
        return Unknown()

    def print_impl(self, printer: Printer) -> None:
        printer.print(self.__class__.__name__ + "()")


@dataclass
class NotAOD(AODState):
    def is_subseteq(self, other: AODState) -> bool:
        return True


@dataclass
class Unknown(AODState):
    def is_subseteq(self, other: AODState) -> bool:
        return isinstance(other, Unknown)


@dataclass
class AOD(AODState):
    x_tones: frozenset[int]
    y_tones: frozenset[int]
    pos: grid.Grid

    def active_positions(self) -> grid.Grid:
        x_indices = ilist.IList(sorted(self.x_tones))
        y_indices = ilist.IList(sorted(self.y_tones))
        return self.pos.get_view(x_indices, y_indices)

    def is_subseteq(self, other: AODState) -> bool:
        # only check of the active AOD positions are equal not necessarily
        # the exact positions
        return (
            isinstance(other, AOD)
            and self.active_positions() == other.active_positions()
        )

from dataclasses import dataclass
from typing import Any

from bloqade.geometry.dialects import grid
from kirin import ir
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
class PythonRuntime(AODState):
    """
    AODState that represents a Python runtime value.
    This is used to represent values that are not known at compile time.
    """

    value: Any

    def is_subseteq(self, other: AODState) -> bool:
        return isinstance(other, PythonRuntime) and self.value == other.value


@dataclass
class AOD(AODState):
    x_tones: frozenset[int]
    y_tones: frozenset[int]
    pos: grid.Grid

    def is_subseteq(self, other: AODState) -> bool:
        return self == other


@dataclass
class AODCollision(AODState):
    x_tones: dict[int, int]
    y_tones: dict[int, int]

    def is_subseteq(self, other: AODState) -> bool:
        return self == other


@dataclass
class AODJump(AODState):
    x_tones: dict[int, tuple[float, float]]
    y_tones: dict[int, tuple[float, float]]

    def is_subseteq(self, other: AODState) -> bool:
        return self == other

from dataclasses import dataclass
from typing import final

from kirin import ir
from kirin.ir.attrs.abc import LatticeAttributeMeta
from kirin.lattice.abc import BoundedLattice
from kirin.lattice.mixin import SimpleJoinMixin, SimpleMeetMixin
from kirin.print.printer import Printer


@dataclass
class Zone(
    ir.Attribute,
    SimpleJoinMixin["Zone"],
    SimpleMeetMixin["Zone"],
    BoundedLattice["Zone"],
    metaclass=LatticeAttributeMeta,
):

    @classmethod
    def bottom(cls) -> "Zone":
        return NotZone()

    @classmethod
    def top(cls) -> "Zone":
        return UnknownZone()

    def print_impl(self, printer: Printer) -> None:
        printer.print(self.__class__.__name__ + "()")


@final
@dataclass
class NotZone(Zone):

    def is_subseteq(self, other: Zone) -> bool:
        return True


@final
@dataclass
class UnknownZone(Zone):

    def is_subseteq(self, other: Zone) -> bool:
        return isinstance(other, UnknownZone)


@dataclass
class InvalidZone(Zone):
    def is_subseteq(self, other: Zone) -> bool:
        return isinstance(other, InvalidZone)

    def join(self, other: Zone) -> Zone:
        return self


@dataclass
class InvalidSpecId(InvalidZone):
    spec_id: str

    def is_subseteq(self, other: Zone) -> bool:
        return isinstance(other, InvalidSpecId) and (self.spec_id == other.spec_id)

    def join(self, other: Zone) -> Zone:
        if isinstance(other, InvalidSpecId):
            if self.spec_id == other.spec_id:
                return self
            else:
                return InvalidZone()

        return Zone.bottom()


@dataclass
class SpecZone(Zone):
    spec_id: str

    def is_subseteq(self, other: Zone) -> bool:
        return isinstance(other, SpecZone) and (self.spec_id == other.spec_id)


@dataclass
class GetItemLike:
    zone: Zone


@dataclass
class GetItemOfZone(GetItemLike, Zone):
    index: Zone

    def is_subseteq(self, other: Zone) -> bool:
        return (
            isinstance(other, GetItemOfZone)
            and self.zone.is_subseteq(other.zone)
            and self.index.is_subseteq(other.index)
        )


@dataclass
class GetSubGridOfZone(GetItemLike, Zone):
    x_indices: Zone
    y_indices: Zone

    def is_subseteq(self, other: Zone) -> bool:
        return (
            isinstance(other, GetSubGridOfZone)
            and self.zone.is_subseteq(other.zone)
            and self.x_indices.is_subseteq(other.x_indices)
            and self.y_indices.is_subseteq(other.y_indices)
        )

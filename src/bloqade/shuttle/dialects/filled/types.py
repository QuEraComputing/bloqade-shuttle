from dataclasses import dataclass, field
from functools import cached_property
from itertools import product
from typing import Any, Iterable, Sequence, TypeVar

from bloqade.geometry.dialects import grid
from kirin import types
from kirin.dialects import ilist

NumX = TypeVar("NumX")
NumY = TypeVar("NumY")


@dataclass
class FilledGrid(grid.Grid[NumX, NumY]):
    x_spacing: tuple[float, ...] = field(init=False)
    y_spacing: tuple[float, ...] = field(init=False)
    x_init: float | None = field(init=False)
    y_init: float | None = field(init=False)

    parent: grid.Grid[NumX, NumY]
    vacant_x: tuple[int, ...]
    vacant_y: tuple[int, ...]

    def __post_init__(self):
        self.x_spacing = self.parent.x_spacing
        self.y_spacing = self.parent.y_spacing
        self.x_init = self.parent.x_init
        self.y_init = self.parent.y_init

        self.type = types.Generic(
            FilledGrid,
            types.Literal(len(self.x_spacing) + 1),
            types.Literal(len(self.y_spacing) + 1),
        )

    def __hash__(self):
        return id(self)

    def is_equal(self, other: Any) -> bool:
        return (
            isinstance(other, FilledGrid)
            and self.parent.is_equal(other.parent)
            and self.vacant_x == other.vacant_x
            and self.vacant_y == other.vacant_y
        )

    @cached_property
    def positions(self) -> ilist.IList[tuple[float, float], Any]:
        positions = tuple(
            (x, y)
            for (ix, x), (iy, y) in product(
                enumerate(self.x_positions), enumerate(self.y_positions)
            )
            if ix not in self.vacant_x and iy not in self.vacant_y
        )

        return ilist.IList(positions)

    @classmethod
    def fill(
        cls, grid_obj: grid.Grid[NumX, NumY], filled: Sequence[tuple[int, int]]
    ) -> "FilledGrid[NumX, NumY]":
        num_x, num_y = grid_obj.shape
        vacancies = (
            (x, y) for x in range(num_x) for y in range(num_y) if (x, y) not in filled
        )

        if isinstance(grid_obj, FilledGrid):
            vacancies = (
                (x, y)
                for x, y in vacancies
                if x not in grid_obj.vacant_x and y not in grid_obj.vacant_y
            )

        vacancies = list(vacancies)
        vacant_x, vacant_y = zip(*vacancies) if vacancies else ((), ())

        return cls(parent=grid_obj, vacant_x=vacant_x, vacant_y=vacant_y)

    @classmethod
    def vacat(
        cls, grid_obj: grid.Grid[NumX, NumY], vacant: Iterable[tuple[int, int]]
    ) -> "FilledGrid[NumX, NumY]":

        if isinstance(grid_obj, FilledGrid):
            vacant = (
                (x, y)
                for x, y in vacant
                if x not in grid_obj.vacant_x and y not in grid_obj.vacant_y
            )

        vacant = sorted(vacant)
        vacant_x, vacant_y = zip(*vacant) if vacant else ((), ())

        return cls(parent=grid_obj, vacant_x=vacant_x, vacant_y=vacant_y)

    def get_parent(self) -> grid.Grid[NumX, NumY]:
        return self.parent

    def get_view(  # type: ignore
        self, x_indices: ilist.IList[int, Any], y_indices: ilist.IList[int, Any]
    ):
        new_vacant_x = tuple(x for x in self.vacant_x if x in x_indices)
        new_vacant_y = tuple(y for y in self.vacant_y if y in y_indices)

        return FilledGrid(
            parent=self.parent.get_view(x_indices, y_indices),
            vacant_x=new_vacant_x,
            vacant_y=new_vacant_y,
        )

    def shift(self, x_shift: float, y_shift: float):
        new_parent = self.parent.shift(x_shift, y_shift)
        return FilledGrid(
            parent=new_parent,
            vacant_x=self.vacant_x,
            vacant_y=self.vacant_y,
        )

    def scale(self, x_scale: float, y_scale: float):
        new_parent = self.parent.scale(x_scale, y_scale)
        return FilledGrid(
            parent=new_parent,
            vacant_x=self.vacant_x,
            vacant_y=self.vacant_y,
        )

    def repeat(self, x_times: int, y_times: int, x_gap: float, y_gap: float):
        new_parent = self.parent.repeat(x_times, y_times, x_gap, y_gap)
        x_dim, y_dim = self.shape
        new_vacant_x = (
            x + x_dim * i
            for i, _, x in product(range(x_times), range(y_times), self.vacant_x)
        )
        new_vacant_y = (
            y + y_dim * j
            for _, j, y in product(range(x_times), range(y_times), self.vacant_y)
        )
        return FilledGrid.vacat(new_parent, zip(new_vacant_x, new_vacant_y))


FilledGridType = types.Generic(FilledGrid, types.TypeVar("NumX"), types.TypeVar("NumY"))

from dataclasses import dataclass, field
from itertools import chain
from typing import cast

import numpy as np
from bloqade.geometry.dialects.grid import Grid
from kirin.interp import Interpreter


@dataclass
class Layout:
    static_traps: dict[str, Grid]
    """Abstract base class for layout."""

    fillable: set[str]
    """The set of trap names that are fillable by the sorter."""

    has_cz: set[str]
    """The set of trap names that can have a CZ gates applied."""

    has_local: set[str]
    """The set of trap names that can have local single qubit gates applied."""

    special_grid: dict[str, Grid] = field(default_factory=dict, kw_only=True)
    """Set of special grid values that are not static traps, but can be used for specific purposes."""

    _zone_to_id: dict[Grid, str] = field(
        default_factory=dict, init=False, compare=False, repr=False
    )

    def __post_init__(self):
        for zone_id, zone in chain(
            self.static_traps.items(), self.special_grid.items()
        ):
            if zone in self._zone_to_id:
                raise ValueError(
                    f"Duplicate static trap zone detected: {zone_id}, {zone}, please ensure all names point to a unique set of locations"
                )

            self._zone_to_id[zone] = zone_id

    def get_zone_id(self, zone: Grid) -> str | None:
        """Get the zone ID for a given grid, if it exists in static_traps or special_grid."""
        return self._zone_to_id.get(zone, None)

    def __hash__(self):
        return hash(
            (
                frozenset(self.static_traps.items()),
                frozenset(self.fillable),
                frozenset(self.has_cz),
                frozenset(self.has_local),
                frozenset(self.special_grid.items()),
            )
        )

    def __eq__(self, other):
        if not isinstance(other, Layout):
            return NotImplemented
        return (
            self.static_traps == other.static_traps and self.fillable == other.fillable
        )

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Get the bounding box (xmin, xmax, ymin, ymax) of the layout."""
        xmin = float("inf")
        xmax = float("-inf")
        ymin = float("inf")
        ymax = float("-inf")

        for zone in chain(self.static_traps.values(), self.special_grid.values()):
            if zone.x_init is not None:
                xmin = min(xmin, zone.x_init)
                xmax = max(xmax, zone.x_init + zone.width)
            if zone.y_init is not None:
                ymin = min(ymin, zone.y_init)
                ymax = max(ymax, zone.y_init + zone.height)

        if (
            xmin == float("inf")
            or xmax == float("-inf")
            or ymin == float("inf")
            or ymax == float("-inf")
        ):
            raise ValueError("Layout has incomplete bounding box data.")

        return xmin, xmax, ymin, ymax

    @staticmethod
    def _plot_zone(zone: Grid, ax, name: str, **plot_options):
        from matplotlib.axes import Axes  # type: ignore
        from matplotlib.patches import Rectangle  # type: ignore

        ax = cast(Axes, ax)

        xs, ys = np.meshgrid(tuple(zone.x_positions), tuple(zone.y_positions))

        path_collection = ax.scatter(xs.ravel(), ys.ravel(), **plot_options)

        width = zone.width + 4
        height = zone.height + 4
        xy = (zone.x_positions[0] - 2, zone.y_positions[0] - 2)

        patch = ax.add_patch(
            Rectangle(
                xy=xy,
                width=width,
                height=height,
                edgecolor=path_collection.get_edgecolor(),
                facecolor="none",
            )
        )
        text_mid = (zone.x_init or 0.0) + zone.width / 2

        ax.text(
            x=text_mid, y=zone.y_positions[-1] + 4, s=name, ha="center", va="center"
        )

        return path_collection, patch

    def fig(self, ax=None):
        from matplotlib import pyplot as plt  # type: ignore

        if ax is None:
            _, ax = plt.subplots(1, 1)

        for zone_id, zone in self.static_traps.items():
            self._plot_zone(zone, ax, zone_id)

        return ax, plt.gcf()

    def show(self, ax=None):
        # impoting this so that matplotlib is optional
        import matplotlib.pyplot as plt  # type: ignore

        ax, fig = self.fig(ax)
        plt.show()


def _default_layout():
    zone = Grid.from_positions(
        range(16),
        range(16),
    ).scale(10.0, 10.0)

    return Layout(
        static_traps={"traps": zone},
        fillable={"traps"},
        has_cz={"traps"},
        has_local={"traps"},
    )


@dataclass(frozen=True)
class ArchSpec:
    layout: Layout = field(default_factory=_default_layout)  # type: ignore
    float_constants: dict[str, float] = field(default_factory=dict)
    int_constants: dict[str, int] = field(default_factory=dict)

    def __hash__(self):
        return hash(
            (
                self.layout,
                frozenset(self.float_constants.items()),
                frozenset(self.int_constants.items()),
            )
        )


@dataclass
class ArchSpecMixin:
    """Base class for interpreters that require an architecture specification."""

    arch_spec: ArchSpec


@dataclass
class ArchSpecInterpreter(ArchSpecMixin, Interpreter):
    """Interpreter that requires an architecture specification."""

    pass

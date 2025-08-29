import warnings
from itertools import repeat

from bloqade.geometry.dialects import grid

from bloqade.shuttle import spec

warnings.warn(
    (
        "This module's contents have been moved to `stdlib.layouts.single_col_zone` submodule and"
        " will be removed in 0.8.0"
    ),
    DeprecationWarning,
)


def single_zone_spec(num_x: int, num_y: int, spacing: float = 10.0) -> spec.ArchSpec:
    """Create a static trap spec with a single zone. compatible with the stdlib

    Args:
        num_x (int): Number of traps in the x direction.
        num_y (int): Number of traps in the y direction.
        spacing (float): Spacing between traps in both directions. Default is 10.0.

    Returns:
        spec.Spec: A specification object containing the layout with a single zone.

    """
    x_spacing = tuple(repeat(spacing, num_x - 1))
    y_spacing = tuple(repeat(spacing, num_y - 1))

    return spec.ArchSpec(
        layout=spec.Layout(
            static_traps={"traps": grid.Grid(x_spacing, y_spacing, 0.0, 0.0)},
            fillable=set(["traps"]),
            has_cz=set(["traps"]),
            has_local=set(["traps"]),
        )
    )

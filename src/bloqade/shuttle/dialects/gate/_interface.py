from typing import Any

from bloqade.geometry.dialects import grid
from kirin.lowering import wraps as _wraps

from .stmts import GlobalR, GlobalRz, LocalR, LocalRz, TopHatCZ


@_wraps(TopHatCZ)
def top_hat_cz(
    zone: grid.Grid[Any, Any],
    upper_buffer: float = 3.0,
    lower_buffer: float = 3.0,
) -> None:
    """Apply a top hat CZ gate.

    Args:
        zone (grid.GridType[Any, Any]): The grid zone where the gate is applied.
        upper_buffer (float): The upper buffer distance for the top hat above the zone.
        lower_buffer (float): The lower buffer distance for the top hat below the zone.

    """
    ...


@_wraps(LocalRz)
def local_rz(rotation_angle: float, zone: grid.Grid[Any, Any]) -> None:
    """Apply a local Rz gate to a zone.

    Args:
        rotation_angle (float): The angle of rotation for the Rz gate.
        zone (grid.GridType[Any, Any]): The grid zone where the gate is applied.

    """
    ...


@_wraps(LocalR)
def local_r(
    axis_angle: float, rotation_angle: float, zone: grid.Grid[Any, Any]
) -> None:
    """Apply a local Rz gate to a zone.

    Args:
        rotation_angle (float): The angle of rotation for the Rz gate.
        zone (grid.GridType[Any, Any]): The grid zone where the gate is applied.

    """
    ...


@_wraps(GlobalR)
def global_r(axis_angle: float, rotation_angle: float):
    """Apply a global R gate over all zones.

    Args:
        axis_angle (float): The angle of the axis for the R gate.
        rotation_angle (float): The angle of rotation for the R gate.

    """
    ...


@_wraps(GlobalRz)
def global_rz(rotation_angle: float):
    """Apply a global Rz gate over all zones.

    Args:
        rotation_angle (float): The angle of rotation for the Rz gate.

    """
    ...

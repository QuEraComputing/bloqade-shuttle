import typing

from bloqade.geometry.dialects import grid
from kirin.lowering import wraps

from bloqade.shuttle.dialects.measure.types import MeasurementArray

from .stmts import Measure

NumX = typing.TypeVar("NumX", bound=int)
NumY = typing.TypeVar("NumY", bound=int)


@wraps(Measure)
def measure(
    regions: tuple[grid.Grid[NumX, NumY], ...],
) -> tuple[MeasurementArray[NumX, NumY], ...]:
    """
    Measure the given regions and return the results.

    Args:
        regions: A tuple of regions to measure.

    Returns:
        A tuple of measurement results.
    """
    ...

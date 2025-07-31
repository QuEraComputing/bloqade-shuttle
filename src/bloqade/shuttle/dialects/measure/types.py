from typing import Generic, TypeVar

from bloqade.squin.qubit import MeasurementResult
from kirin import types

NumRows = TypeVar("NumRows")
NumCols = TypeVar("NumCols")


class MeasurementArray(Generic[NumRows, NumCols]):

    def __getitem__(self, indices: tuple[int, int]) -> MeasurementResult:
        """
        Get a measurement result from the array using the given indices.
        """
        raise NotImplementedError(
            "This Class is a placeholder and should be replaced with the actual implementation."
        )


MeasurementArrayType = types.Generic(
    MeasurementArray, types.TypeVar("NumRows"), types.TypeVar("NumCols")
)

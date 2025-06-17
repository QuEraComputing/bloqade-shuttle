from typing import Generic, TypeVar

from kirin import types


# TODO: replace this with the squin dialect's MeasurementResultType
class MeasurementResult:
    pass


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


MeasurementResultType = types.PyClass(MeasurementResult)
MeasurementArrayType = types.Generic(
    MeasurementArray, types.TypeVar("NumRows"), types.TypeVar("NumCols")
)

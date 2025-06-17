from typing import TypeVar

from bloqade.qourier.dialects.measure import (
    Measure,
    dialect,
)
from bloqade.qourier.visualizer.interp import PathVisualizer
from bloqade.qourier.visualizer.renderers import RendererInterface
from kirin import interp


class MeasureResultRuntime:
    pass


@dialect.register(key="path.visualizer")
class MeasureVisualizerMethods(interp.MethodTable):

    Renderer = TypeVar("Renderer", bound="RendererInterface")

    @interp.impl(Measure)
    def fill(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: Measure
    ):
        return (MeasureResultRuntime(),)

from typing import TypeVar

from kirin import interp

from bloqade.shuttle.dialects.measure import (
    Measure,
    dialect,
)
from bloqade.shuttle.visualizer.interp import PathVisualizer
from bloqade.shuttle.visualizer.renderers import RendererInterface


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

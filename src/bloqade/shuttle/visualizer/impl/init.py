from typing import TypeVar

from bloqade.qourier.dialects.init import Fill, dialect
from bloqade.qourier.visualizer.interp import PathVisualizer
from bloqade.qourier.visualizer.renderers import RendererInterface
from kirin import interp


@dialect.register(key="path.visualizer")
class InitVisualizerMethods(interp.MethodTable):

    Renderer = TypeVar("Renderer", bound=RendererInterface)

    @interp.impl(Fill)
    def fill(self, _interp: PathVisualizer[Renderer], frame: interp.Frame, stmt: Fill):
        return ()

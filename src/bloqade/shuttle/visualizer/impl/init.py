from typing import TypeVar

from kirin import interp

from bloqade.shuttle.dialects.init import Fill, dialect
from bloqade.shuttle.visualizer.interp import PathVisualizer
from bloqade.shuttle.visualizer.renderers import RendererInterface


@dialect.register(key="path.visualizer")
class InitVisualizerMethods(interp.MethodTable):

    Renderer = TypeVar("Renderer", bound=RendererInterface)

    @interp.impl(Fill)
    def fill(self, _interp: PathVisualizer[Renderer], frame: interp.Frame, stmt: Fill):
        return ()

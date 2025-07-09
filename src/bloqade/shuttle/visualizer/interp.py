from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

from typing_extensions import Self

from bloqade.shuttle.arch import ArchSpecInterpreter

if TYPE_CHECKING:
    from bloqade.shuttle.visualizer.renderers import RendererInterface


def default_renderer():
    from bloqade.shuttle.visualizer.renderers.matplotlib import MatplotlibRenderer

    return MatplotlibRenderer()


Plotter = TypeVar("Plotter", bound="RendererInterface")


@dataclass
class PathVisualizer(ArchSpecInterpreter, Generic[Plotter]):
    """Debugging interpreter for visualizing the execution of paths."""

    keys = ["path.visualizer", "spec.interp", "main"]
    renderer: Plotter = field(kw_only=True, default_factory=default_renderer, repr=False)  # type: ignore

    def initialize(self) -> Self:
        for zone_id, zone in self.arch_spec.layout.static_traps.items():
            self.renderer.render_traps(zone, zone_id)

        return super().initialize()

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

from kirin import interp, ir
from typing_extensions import Self

from bloqade.shuttle.dialects import spec
from bloqade.shuttle.passes import inject_spec

if TYPE_CHECKING:
    from bloqade.shuttle.visualizer.renderers import RendererInterface


def default_renderer():
    from bloqade.shuttle.visualizer.renderers.matplotlib import MatplotlibRenderer

    return MatplotlibRenderer()


Plotter = TypeVar("Plotter", bound="RendererInterface")


@dataclass
class PathVisualizer(interp.Interpreter, Generic[Plotter]):
    """Debugging interpreter for visualizing the execution of paths."""

    keys = ["path.visualizer", "main"]
    arch_spec: spec.Spec = field(kw_only=True)
    renderer: Plotter = field(kw_only=True, default_factory=default_renderer, repr=False)  # type: ignore

    def initialize(self) -> Self:
        for zone_id, zone in self.arch_spec.layout.static_traps.items():
            self.renderer.render_traps(zone, zone_id)

        return super().initialize()

    def run(self, mt: ir.Method, args: tuple, kwargs: dict | None = None) -> None:
        inject_spec.InjectSpecsPass(mt.dialects, self.arch_spec)(mt := mt.similar())
        super().run(mt, args, kwargs=kwargs)

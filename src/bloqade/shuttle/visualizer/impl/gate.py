from typing import TypeVar

from kirin import interp

from bloqade.shuttle.dialects.gate import (
    GlobalR,
    GlobalRz,
    LocalR,
    LocalRz,
    TopHatCZ,
    dialect,
)
from bloqade.shuttle.visualizer.interp import PathVisualizer
from bloqade.shuttle.visualizer.renderers import RendererInterface


@dialect.register(key="path.visualizer")
class GateVisualizerMethods(interp.MethodTable):

    Renderer = TypeVar("Renderer", bound="RendererInterface")

    @interp.impl(TopHatCZ)
    def fill(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: TopHatCZ
    ):
        _interp.renderer.top_hat_cz(
            frame.get(stmt.zone), stmt.upper_buffer, stmt.lower_buffer
        )
        return ()

    @interp.impl(LocalR)
    def local_r(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: LocalR
    ):
        _interp.renderer.local_r(frame.get(stmt.zone))
        return ()

    @interp.impl(LocalRz)
    def local_rz(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: LocalRz
    ):
        _interp.renderer.local_rz(frame.get(stmt.zone))
        return ()

    @interp.impl(GlobalR)
    def global_r(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: GlobalR
    ):
        _interp.renderer.global_r()
        return ()

    @interp.impl(GlobalRz)
    def global_rz(
        self, _interp: "PathVisualizer[Renderer]", frame: interp.Frame, stmt: GlobalRz
    ):
        _interp.renderer.global_rz()
        return ()

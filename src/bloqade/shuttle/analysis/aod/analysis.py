from dataclasses import dataclass
from typing import Any

from kirin import interp, ir
from kirin.analysis.forward import Forward, ForwardFrame

from bloqade.shuttle.dialects import tracking

from .lattice import AODState


@dataclass
class AODAnalysis(Forward[AODState]):

    keys = ["aod.analysis"]
    lattice = AODState

    max_x_tones: int
    max_y_tones: int

    def get_const_value(self, typ, ssa: ir.SSAValue) -> Any | None:
        raise NotImplementedError

    def eval_stmt_fallback(
        self, frame: ForwardFrame[AODState], stmt: ir.Statement
    ) -> tuple[AODState, ...] | interp.SpecialValue[AODState]:
        return tuple(
            AODState.top()
            for result in stmt.results
            if result.type.is_subseteq(tracking.SystemStateType)
        )

    def run_method(self, method: ir.Method, args: tuple[AODState, ...]):
        # NOTE: we do not support dynamic calls here, thus no need to propagate method object
        return self.run_callable(method.code, (self.lattice.bottom(),) + args)

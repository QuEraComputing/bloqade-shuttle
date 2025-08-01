from dataclasses import dataclass

from kirin import interp, ir
from kirin.analysis.forward import Forward, ForwardFrame

from bloqade.shuttle.dialects import tracking

from .lattice import AODState


@dataclass
class AODStateAnalysis(Forward[AODState]):

    keys = ["aod.analysis"]
    lattice = AODState

    max_x_tones: int
    max_y_tones: int

    def is_pure(self, stmt: ir.Statement) -> bool:
        # Check if the statement is pure by looking at its attributes

        return (
            stmt.has_trait(ir.Pure)
            or (maybe_pure := stmt.get_trait(ir.MaybePure)) is not None
            and maybe_pure.is_pure(stmt)
        )

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

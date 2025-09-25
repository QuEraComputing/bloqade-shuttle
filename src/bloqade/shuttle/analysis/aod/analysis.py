from dataclasses import dataclass
from typing import Type, TypeVar

from kirin import interp, ir
from kirin.analysis import const
from kirin.analysis.forward import Forward, ForwardFrame

from bloqade.shuttle.arch import ArchSpecMixin
from bloqade.shuttle.dialects import tracking

from .lattice import AODState


@dataclass
class AODAnalysis(Forward[AODState], ArchSpecMixin):

    keys = ["aod.analysis", "spec.interp"]
    lattice = AODState

    T = TypeVar("T")

    def get_const_value(self, typ: Type[T], ssa: ir.SSAValue) -> T:
        if not isinstance(value := ssa.hints.get("const"), const.Value):
            raise interp.InterpreterError(
                "Non-constant value encountered in AOD analysis."
            )

        if not isinstance(data := value.data, typ):
            raise interp.InterpreterError(
                f"Expected constant of type {typ}, got {type(data)}."
            )

        return data

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

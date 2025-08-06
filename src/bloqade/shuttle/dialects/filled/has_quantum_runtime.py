from kirin import interp

from bloqade.shuttle.analysis.has_quantum_runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import Fill


@dialect.register(key="has_quantum_runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(Fill)
    def gate(
        self, interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: Fill
    ) -> interp.StatementResult[RuntimeFrame]:
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        return ()

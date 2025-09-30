from kirin import interp

from bloqade.shuttle.analysis.runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import Fill


@dialect.register(key="runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(Fill)
    def gate(self, interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: Fill):
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        frame.quantum_stmts.add(stmt)
        return ()

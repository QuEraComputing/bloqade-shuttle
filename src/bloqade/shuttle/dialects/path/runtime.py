from kirin import interp

from bloqade.shuttle.analysis.runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import Play


@dialect.register(key="runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(Play)
    def gate(
        self, interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: Play
    ) -> interp.StatementResult[RuntimeFrame]:
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        frame.quantum_stmts.add(stmt)
        return ()

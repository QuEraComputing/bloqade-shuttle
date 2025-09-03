from kirin import interp

from bloqade.shuttle.analysis.runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import Measure


@dialect.register(key="runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(Measure)
    def gate(self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: Measure):
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        frame.quantum_stmts.add(stmt)
        return (_interp.lattice.top(),)

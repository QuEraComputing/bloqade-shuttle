from kirin import interp
from kirin.lattice import EmptyLattice

from bloqade.shuttle.analysis.has_quantum_runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import Measure


@dialect.register(key="has_quantum_runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(Measure)
    def gate(
        self, interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: Measure
    ) -> interp.StatementResult[EmptyLattice]:
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        return (EmptyLattice.top(),)

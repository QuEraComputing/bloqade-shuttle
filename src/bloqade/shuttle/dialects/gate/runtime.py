from kirin import interp

from bloqade.shuttle.analysis.runtime import (
    RuntimeAnalysis,
    RuntimeFrame,
)

from ._dialect import dialect
from .stmts import GlobalR, GlobalRz, LocalR, LocalRz, TopHatCZ


@dialect.register(key="runtime")
class HasQuantumRuntimeMethodTable(interp.MethodTable):

    @interp.impl(TopHatCZ)
    @interp.impl(LocalRz)
    @interp.impl(LocalR)
    @interp.impl(GlobalR)
    @interp.impl(GlobalRz)
    def gate(
        self,
        interp: RuntimeAnalysis,
        frame: RuntimeFrame,
        stmt: TopHatCZ | LocalRz | LocalR | GlobalR | GlobalRz,
    ) -> interp.StatementResult[RuntimeFrame]:
        """Handle gate statements and mark the frame as quantum."""
        frame.is_quantum = True
        frame.quantum_stmts.add(stmt)
        return ()

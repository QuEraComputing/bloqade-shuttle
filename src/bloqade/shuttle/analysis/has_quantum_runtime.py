from dataclasses import dataclass, field

from kirin import ir
from kirin.analysis import ForwardExtra, ForwardFrame
from kirin.lattice import EmptyLattice


@dataclass
class RuntimeFrame(ForwardFrame[EmptyLattice]):
    """Frame for quantum runtime analysis.

    This frame is used to track the quantum runtime information during the
    forward dataflow analysis.
    """

    is_quantum: bool = False
    """Flag to indicate if the frame has no quantum runtime inside it."""
    quantum_stmts: set[ir.Statement] = field(default_factory=set)


class RuntimeAnalysis(ForwardExtra[RuntimeFrame, EmptyLattice]):
    """Forward dataflow analysis to check if a method has quantum runtime.

    This analysis checks if a method contains any quantum runtime operations.
    It is used to determine if the method can be executed on a quantum device.
    """

    keys = ["has_quantum_runtime"]
    lattice = EmptyLattice

    def eval_stmt_fallback(self, frame: RuntimeFrame, stmt: ir.Statement):
        return tuple(EmptyLattice.top() for _ in stmt.results)

    def initialize_frame(
        self, code: ir.Statement, *, has_parent_access: bool = False
    ) -> RuntimeFrame:
        return RuntimeFrame(code, has_parent_access=has_parent_access)

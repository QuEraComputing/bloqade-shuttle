from dataclasses import dataclass, field

from kirin import interp, ir
from kirin.analysis import ForwardExtra, ForwardFrame
from kirin.dialects import func, scf
from kirin.lattice import EmptyLattice


@dataclass
class RuntimeFrame(ForwardFrame[EmptyLattice]):
    """Frame for quantum runtime analysis.
    This frame is used to track the state of quantum operations within a method.
    """

    quantum_stmts: set[ir.Statement] = field(default_factory=set)
    """Set of quantum statements in the frame."""
    is_quantum: bool = False
    """Whether the frame contains quantum operations."""


class RuntimeAnalysis(ForwardExtra[RuntimeFrame, EmptyLattice]):
    """Forward dataflow analysis to check if a method has quantum runtime.

    This analysis checks if a method contains any quantum runtime operations.
    It is used to determine if the method can be executed on a quantum device.
    """

    keys = ["runtime"]
    lattice = EmptyLattice

    def eval_stmt_fallback(self, frame: RuntimeFrame, stmt: ir.Statement):
        return tuple(EmptyLattice.top() for _ in stmt.results)

    def initialize_frame(
        self, code: ir.Statement, *, has_parent_access: bool = False
    ) -> RuntimeFrame:
        return RuntimeFrame(code, has_parent_access=has_parent_access)

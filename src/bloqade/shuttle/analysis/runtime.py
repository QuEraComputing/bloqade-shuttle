from dataclasses import dataclass, field

from kirin import ir
from kirin.analysis import ForwardExtra, ForwardFrame
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

        is_quantum = False
        stmts = set()

        for region in stmt.regions:
            with self.new_frame(stmt, has_parent_access=True) as new_frame:
                args = tuple(EmptyLattice.top() for _ in region.blocks[0].args)
                self.run_callable_region(new_frame, stmt, region, args)

            stmts |= new_frame.quantum_stmts
            is_quantum |= new_frame.is_quantum

        frame.quantum_stmts |= stmts
        frame.is_quantum |= is_quantum

        if is_quantum:
            frame.quantum_stmts.add(stmt)

        return tuple(EmptyLattice.top() for _ in stmt.results)

    def initialize_frame(
        self, code: ir.Statement, *, has_parent_access: bool = False
    ) -> RuntimeFrame:
        return RuntimeFrame(code, has_parent_access=has_parent_access)

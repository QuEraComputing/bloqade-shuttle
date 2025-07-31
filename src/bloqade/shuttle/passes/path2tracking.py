from dataclasses import dataclass, field

from kirin import ir
from kirin.dialects import cf, func
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.dialects import gate, init, measure, path
from bloqade.shuttle.dialects.tracking.types import SystemStateType


@dataclass
class Path2TrackingRewrite(RewriteRule):
    entry_code: func.Function
    curr_state: ir.SSAValue | None = None
    callgraph: dict[ir.Method, ir.Method] = field(default_factory=dict)

    stmt_types = (
        path.Play,
        gate.TopHatCZ,
        gate.GlobalR,
        gate.LocalR,
        measure.Measure,
        cf.ConditionalBranch,
        cf.Branch,
        func.Function,
        func.Return,
        func.Lambda,
        init.Fill,
    )

    def default_rewrite(self, node: ir.Statement) -> RewriteResult:
        raise RuntimeError(f"missing rewrite method for statement type {type(node)!r}")

    def rewrite_Block(self, node: ir.Block) -> RewriteResult:
        if (region := node.parent_node) is None:
            return RewriteResult()

        if node.parent_node is self.entry_code and (region._block_idx[node] == 0):
            return RewriteResult()

        if self.curr_state is None:
            return RewriteResult()

        self.curr_state = node.args.insert_from(0, SystemStateType, "system_state")
        return RewriteResult(has_done_something=True)

    def rewrite_Statement(self, node: ir.Statement) -> RewriteResult:
        if not isinstance(node, self.stmt_types):
            return RewriteResult()

        method = getattr(self, f"rewrite_{type(node).__name__}", self.default_rewrite)
        return method(node)

    def rewrite_Fill(self, node: init.Fill) -> RewriteResult:
        assert (
            self.curr_state is not None
        ), "curr_state should not be set before Fill is rewritten"

        return RewriteResult()

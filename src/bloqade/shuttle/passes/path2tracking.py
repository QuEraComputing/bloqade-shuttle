from dataclasses import dataclass, field

from kirin import ir, rewrite, types
from kirin.dialects import cf, func, scf
from kirin.passes import Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.dialects import gate, init, measure, path, tracking
from bloqade.shuttle.dialects.tracking.types import SystemStateType


@dataclass
class PathToTrackingRewrite(RewriteRule):
    entry_code: func.Function
    curr_state: ir.SSAValue | None = None
    call_graph: dict[ir.Method, ir.Method] = field(default_factory=dict)

    stmt_types = (
        path.Play,
        gate.TopHatCZ,
        gate.GlobalR,
        gate.LocalR,
        measure.Measure,
        init.Fill,
        cf.ConditionalBranch,
        cf.Branch,
        scf.For,
        scf.IfElse,
        scf.Yield,
        func.Function,
        func.Return,
        func.Lambda,
        func.Invoke,
    )

    def default_rewrite(self, node: ir.Statement) -> RewriteResult:
        raise RuntimeError(f"missing rewrite method for statement type {type(node)!r}")

    def rewrite_Block(self, node: ir.Block) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        if (region := node.parent_node) is None:
            return RewriteResult()

        if node.parent_node is self.entry_code and (region._block_idx[node] == 0):
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
            self.curr_state is None
        ), "curr_state should not be set before Fill is rewritten"

        node.replace_by(new_node := tracking.Fill(node.locations))

        self.curr_state = new_node.result

        return RewriteResult(has_done_something=True)

    def rewrite_Play(self, node: path.Play) -> RewriteResult:
        assert (
            self.curr_state is not None
        ), "curr_state should be set before Play is rewritten"

        node.replace_by(
            new_node := tracking.Play(state=self.curr_state, path=node.path)
        )
        self.curr_state = new_node.result
        return RewriteResult(has_done_something=True)

    def rewrite_TopHatCZ(self, node: gate.TopHatCZ) -> RewriteResult:
        assert (
            self.curr_state is not None
        ), "curr_state should be set before TopHatCZ is rewritten"

        node.replace_by(
            new_node := tracking.TopHatCZ(state=self.curr_state, zone=node.zone)
        )
        self.curr_state = new_node.result

        return RewriteResult(has_done_something=True)

    def rewrite_GlobalR(self, node: gate.GlobalR) -> RewriteResult:
        assert (
            self.curr_state is not None
        ), "curr_state should be set before GlobalR is rewritten"

        node.replace_by(
            new_node := tracking.GlobalR(
                state=self.curr_state,
                axis_angle=node.axis_angle,
                rotation_angle=node.rotation_angle,
            )
        )
        self.curr_state = new_node.result

        return RewriteResult(has_done_something=True)

    def rewrite_LocalR(self, node: gate.LocalR) -> RewriteResult:
        assert (
            self.curr_state is not None
        ), "curr_state should be set before LocalR is rewritten"

        node.replace_by(
            new_node := tracking.LocalR(
                state=self.curr_state,
                axis_angle=node.axis_angle,
                rotation_angle=node.rotation_angle,
                zone=node.zone,
            )
        )
        self.curr_state = new_node.result

        return RewriteResult(has_done_something=True)

    def rewrite_Measure(self, node: measure.Measure) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.insert_before(
            new_node := tracking.Measure(state=self.curr_state, grids=node.grids)
        )
        self.curr_state = new_node.results[0]

        for old_result, new_result in zip(node.results, new_node.results[1:]):
            old_result.replace_by(new_result)

        node.delete()

        return RewriteResult(has_done_something=True)

    def rewrite_Branch(self, node: cf.Branch) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.replace_by(
            cf.Branch(
                arguments=(self.curr_state, *node.arguments),
                successor=node.successor,
            )
        )
        return RewriteResult(has_done_something=True)

    def rewrite_ConditionalBranch(self, node: cf.ConditionalBranch) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.replace_by(
            cf.ConditionalBranch(
                node.cond,
                (self.curr_state, *node.then_arguments),
                (self.curr_state, *node.else_arguments),
                then_successor=node.then_successor,
                else_successor=node.else_successor,
            )
        )
        return RewriteResult(has_done_something=True)

    def rewrite_For(self, node: scf.For) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.replace_by(
            scf.For(
                node.iterable,
                node.body,  # body will be rewritten in the `rewrite_Block` method
                self.curr_state,
                *node.initializers,
            )
        )
        return RewriteResult(has_done_something=True)

    def rewrite_Yield(self, node: scf.Yield) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.replace_by(
            scf.Yield(
                self.curr_state,
                *node.values,
            )
        )

        return RewriteResult(has_done_something=True)

    def rewrite_Return(self, node: func.Return) -> RewriteResult:
        if node.parent_stmt is self.entry_code or node.parent_stmt is None:
            return RewriteResult()

        raise RuntimeError("missing rewrite method for Return statement")

    def rewrite_Function(self, node: func.Function) -> RewriteResult:
        if node is self.entry_code:
            return RewriteResult()

        old_signature = node.signature
        new_signature = func.Signature(
            (SystemStateType, *old_signature.inputs),
            types.Tuple[SystemStateType, old_signature.output],
        )

        node.replace_by(
            func.Function(
                sym_name=node.sym_name,
                signature=new_signature,
                body=node.body,
            )
        )

        return RewriteResult(has_done_something=True)

    def rewrite_Lambda(self, node: func.Lambda) -> RewriteResult:
        if node is self.entry_code:
            return RewriteResult()

        old_signature = node.signature
        new_signature = func.Signature(
            (SystemStateType, *old_signature.inputs),
            types.Tuple[SystemStateType, old_signature.output],
        )

        node.replace_by(
            func.Lambda(
                node.captured,
                sym_name=node.sym_name,
                signature=new_signature,
                body=node.body,
            )
        )

        return RewriteResult(has_done_something=True)

    def rewrite_Call(self, node: func.Call) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        node.replace_by(
            func.Call(
                node.callee,
                (self.curr_state, *node.inputs),
                kwargs=node.kwargs,
            )
        )

        return RewriteResult(has_done_something=True)

    def rewrite_Invoke(self, node: func.Invoke) -> RewriteResult:
        if self.curr_state is None:
            return RewriteResult()

        callee = node.callee
        if callee not in self.call_graph:
            new_callee = callee.similar()
            self.call_graph[callee] = new_callee
            new_callee.arg_names = ["system_state", *callee.arg_names]

            rewrite.Walk(self).rewrite(new_callee.code)
        else:
            new_callee = self.call_graph[callee]

        node.replace_by(
            func.Invoke(
                (self.curr_state, *node.inputs),
                callee=new_callee,
                kwargs=node.kwargs,
            )
        )

        return RewriteResult(has_done_something=True)


@dataclass
class PathToTracking(Pass):
    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        if not isinstance(mt.code, func.Function):
            return RewriteResult()

        return rewrite.Walk(PathToTrackingRewrite(mt.code)).rewrite(mt.code)

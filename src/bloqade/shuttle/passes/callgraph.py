from dataclasses import dataclass

from kirin import ir, passes
from kirin.dialects import func
from kirin.passes import Pass
from kirin.rewrite import Walk
from kirin.rewrite.abc import RewriteResult, RewriteRule


@dataclass
class ReplaceMethods(RewriteRule):
    new_symbols: dict[ir.Method, ir.Method]

    def rewrite_Statement(self, node: ir.Statement) -> RewriteResult:
        if (
            not isinstance(node, func.Invoke)
            or (new_callee := self.new_symbols.get(node.callee)) is None
        ):
            return RewriteResult()

        node.replace_by(
            func.Invoke(
                callee=new_callee,
                inputs=node.inputs,
                kwargs=node.kwargs,
            )
        )

        return RewriteResult(has_done_something=True)


@dataclass
class CallGraphPass(Pass):
    """Copy all functions in the call graph and apply a rule to each of them."""

    rule: RewriteRule
    """The rule to apply to each function in the call graph."""

    def methods_on_callgraph(self, mt: ir.Method) -> set[ir.Method]:

        callees = set([mt])
        for stmt in mt.callable_region.walk():
            if isinstance(stmt, func.Invoke):
                print(f"Found callee: {stmt.callee.sym_name}")
                if stmt.callee not in callees:
                    callees.update(self.methods_on_callgraph(stmt.callee))

        return callees

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        result = RewriteResult()
        mt_map = {}

        subroutines = self.methods_on_callgraph(mt)
        for original_mt in subroutines:
            if original_mt is mt:
                new_mt = original_mt
            else:
                new_mt = original_mt.similar()
            result = self.rule.rewrite(new_mt.code).join(result)
            mt_map[original_mt] = new_mt

        if result.has_done_something:
            for _, new_mt in mt_map.items():
                Walk(ReplaceMethods(mt_map)).rewrite(new_mt.code)
                passes.Fold(self.dialects)(new_mt)

        return result

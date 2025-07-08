from dataclasses import dataclass, field

from kirin import ir, rewrite
from kirin.dialects import func, py
from kirin.dialects.py import Constant
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Fold, HintConst, Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.dialects import spec


@dataclass
class InjectStaticTrapsRule(RewriteRule):
    arch_spec: spec.Spec
    visited: dict[ir.Method, ir.Method] = field(default_factory=dict, init=False)
    worklist: list[ir.Method] = field(default_factory=list, init=False)

    def get(self, mt: ir.Method):
        if mt in self.visited:
            return self.visited[mt]

        # make sure to mark this method as visited
        self.visited[mt] = (new_mt := mt.similar())
        rewrite.Walk(self).rewrite(new_mt.code)

        return new_mt

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        if isinstance(node, py.Constant) and isinstance(
            mt := node.value.unwrap(), ir.Method
        ):
            new_mt = self.get(mt)
            node.replace_by(Constant(new_mt))
            return RewriteResult(has_done_something=True)
        elif isinstance(node, func.Invoke):
            new_callee = self.get(node.callee)
            node.replace_by(
                func.Invoke(
                    node.inputs,
                    callee=new_callee,
                    kwargs=node.kwargs,
                    purity=node.purity,
                )
            )
        elif isinstance(node, spec.GetStaticTrap):
            zone_id = node.zone_id
            if zone_id not in self.arch_spec.layout.static_traps:
                return RewriteResult()

            node.replace_by(Constant(self.arch_spec.layout.static_traps[zone_id]))

            return RewriteResult(has_done_something=True)

        return RewriteResult()


@dataclass
class InjectSpecsPass(Pass):
    arch_spec: spec.Spec
    fold: bool = True

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        result = rewrite.Walk(InjectStaticTrapsRule(self.arch_spec)).rewrite(mt.code)
        if self.fold:
            result = HintConst(mt.dialects)(mt).join(result)
            result = Fold(mt.dialects)(mt).join(result)

        return result

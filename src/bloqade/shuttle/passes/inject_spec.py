from dataclasses import dataclass

from kirin import ir, rewrite
from kirin.dialects import func
from kirin.dialects.py import Constant
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Fold, HintConst, Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.dialects import path, spec
from bloqade.shuttle.spec import ArchSpec


@dataclass
class InjectStaticTrapsRule(RewriteRule):
    arch_spec: ArchSpec
    visited: dict[ir.Method, ir.Method]

    def get(self, mt: ir.Method):
        if mt in self.visited:
            return self.visited[mt]

        # make sure to mark this method as visited to handle recursive calls
        self.visited[mt] = (new_mt := mt.similar())
        rewrite.Walk(self).rewrite(new_mt.code)
        return new_mt

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        if (
            isinstance(node, func.Invoke)
            and (callee := self.get(node.callee)) is not node.callee
        ):
            node.replace_by(
                func.Invoke(
                    node.inputs,
                    callee=callee,
                    kwargs=node.kwargs,
                    purity=node.purity,
                )
            )
        elif (
            isinstance(node, spec.GetStaticTrap)
            and (zone_id := node.zone_id) in self.arch_spec.layout.static_traps
        ):
            node.replace_by(Constant(self.arch_spec.layout.static_traps[zone_id]))

            return RewriteResult(has_done_something=True)
        elif isinstance(node, path.Gen) and node.arch_spec is None:
            node.arch_spec = self.arch_spec
            return RewriteResult(has_done_something=True)

        return RewriteResult()


@dataclass
class InjectSpecsPass(Pass):
    arch_spec: ArchSpec
    fold: bool = True

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        # since we're rewriting `mt` inplace we should make sure it is on the visited list
        # so that recursive calls are handed correctly
        result = rewrite.Walk(InjectStaticTrapsRule(self.arch_spec, {mt: mt})).rewrite(
            mt.code
        )
        if self.fold:
            result = HintConst(mt.dialects)(mt).join(result)
            result = Fold(mt.dialects)(mt).join(result)

        return result

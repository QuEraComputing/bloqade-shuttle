from dataclasses import dataclass

from kirin import ir, rewrite
from kirin.dialects.py import Constant
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Fold, HintConst, Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.arch import ArchSpec
from bloqade.shuttle.dialects import path, spec
from bloqade.shuttle.passes.callgraph import CallGraphPass


@dataclass
class InjectSpecRule(RewriteRule):
    arch_spec: ArchSpec
    visited: dict[ir.Method, ir.Method]

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        if isinstance(node, path.Gen) and node.arch_spec is None:
            node.arch_spec = self.arch_spec
            return RewriteResult(has_done_something=True)
        elif (
            isinstance(node, spec.GetStaticTrap)
            and (zone_id := node.zone_id) in self.arch_spec.layout.static_traps
        ):
            node.replace_by(Constant(self.arch_spec.layout.static_traps[zone_id]))

            return RewriteResult(has_done_something=True)
        else:
            return RewriteResult()


@dataclass
class InjectSpecsPass(Pass):
    arch_spec: ArchSpec
    fold: bool = True

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        # since we're rewriting `mt` inplace we should make sure it is on the visited list
        # so that recursive calls are handed correctly
        rule = rewrite.Walk(InjectSpecRule(self.arch_spec, {mt: mt}))
        result = CallGraphPass(mt.dialects, rule)(mt)
        if self.fold:
            result = HintConst(mt.dialects)(mt).join(result)
            result = Fold(mt.dialects)(mt).join(result)

        return result

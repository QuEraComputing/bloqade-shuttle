from dataclasses import dataclass, field

from kirin import ir, rewrite
from kirin.dialects.py import Constant
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Fold, Pass
from kirin.passes.callgraph import CallGraphPass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle.arch import ArchSpec
from bloqade.shuttle.dialects import path, spec


@dataclass
class InjectSpecRule(RewriteRule):
    arch_spec: ArchSpec

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
        elif (
            isinstance(node, spec.GetIntConstant)
            and node.constant_id in self.arch_spec.int_constants
        ):
            node.replace_by(Constant(self.arch_spec.int_constants[node.constant_id]))
            return RewriteResult(has_done_something=True)
        elif (
            isinstance(node, spec.GetFloatConstant)
            and node.constant_id in self.arch_spec.float_constants
        ):
            node.replace_by(Constant(self.arch_spec.float_constants[node.constant_id]))
            return RewriteResult(has_done_something=True)

        return RewriteResult()


@dataclass
class InjectSpecsPass(Pass):
    arch_spec: ArchSpec
    fold: bool = True
    fold_pass: Fold = field(init=False)

    def __post_init__(self):
        self.fold_pass = Fold(self.dialects, no_raise=self.no_raise)

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        # since we're rewriting `mt` inplace we should make sure it is on the visited list
        # so that recursive calls are handed correctly
        rule = rewrite.Walk(InjectSpecRule(self.arch_spec))
        result = CallGraphPass(self.dialects, rule, no_raise=self.no_raise).unsafe_run(
            mt
        )
        if self.fold:
            result = self.fold_pass(mt).join(result)

        return result

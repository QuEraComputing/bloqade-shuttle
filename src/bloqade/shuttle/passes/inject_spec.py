from dataclasses import dataclass, field

from kirin import rewrite
from kirin.dialects.py import Constant
from kirin.ir.method import Method
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Fold, HintConst, Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.qourier.dialects import spec


@dataclass
class InjectStaticTrapsRule(RewriteRule):
    arch_spec: spec.Spec = field(default_factory=spec.Spec)
    layout: spec.Layout = field(init=False)

    def __post_init__(self):
        self.layout = self.arch_spec.layout

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        if not isinstance(node, spec.GetStaticTrap):
            return RewriteResult()

        zone_id = node.zone_id
        if zone_id not in self.layout.static_traps:
            return RewriteResult()

        node.replace_by(Constant(self.layout.static_traps[zone_id]))

        return RewriteResult(has_done_something=True)


@dataclass
class InjectSpecsPass(Pass):
    arch_spec: spec.Spec
    fold: bool = True

    def unsafe_run(self, mt: Method) -> RewriteResult:
        result = rewrite.Walk(InjectStaticTrapsRule(self.arch_spec)).rewrite(mt.code)
        if self.fold:
            result = HintConst(mt.dialects)(mt).join(result)
            result = Fold(mt.dialects)(mt).join(result)

        return result

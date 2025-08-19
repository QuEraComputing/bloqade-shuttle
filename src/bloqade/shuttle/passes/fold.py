from dataclasses import dataclass, field

from kirin import ir
from kirin.dialects import ilist, scf
from kirin.ir.method import Method
from kirin.passes import HintConst, Pass, TypeInfer
from kirin.rewrite import (
    Call2Invoke,
    CFGCompactify,
    Chain,
    ConstantFold,
    DeadCodeElimination,
    Fixpoint,
    Inline,
    InlineGetField,
    InlineGetItem,
    Walk,
)
from kirin.rewrite.abc import RewriteResult
from kirin.rewrite.cse import CommonSubexpressionElimination


@dataclass
class AggressiveUnroll(Pass):
    """Fold pass to fold control flow"""

    constprop: HintConst = field(init=False)
    typeinfer: TypeInfer = field(init=False)

    def __post_init__(self):
        self.const_hint = HintConst(self.dialects, no_raise=self.no_raise)
        self.typeinfer = TypeInfer(self.dialects, no_raise=self.no_raise)

    def unsafe_run(self, mt: Method) -> RewriteResult:
        result = RewriteResult()
        result = self.const_hint.unsafe_run(mt).join(result)
        rule = Chain(
            ConstantFold(),
            Call2Invoke(),
            InlineGetField(),
            InlineGetItem(),
            ilist.rewrite.InlineGetItem(),
            DeadCodeElimination(),
            CommonSubexpressionElimination(),
        )
        result = Fixpoint(Walk(rule)).rewrite(mt.code).join(result)
        result = (
            Walk(
                Chain(
                    scf.unroll.PickIfElse(),
                    scf.unroll.ForLoop(),
                    scf.trim.UnusedYield(),
                )
            )
            .rewrite(mt.code)
            .join(result)
        )

        self.typeinfer.unsafe_run(mt)
        result = (
            Walk(Chain(ilist.rewrite.ConstList2IList(), ilist.rewrite.Unroll()))
            .rewrite(mt.code)
            .join(result)
        )

        result = Walk(Inline(self.inline_heuristic)).rewrite(mt.code).join(result)
        result = Walk(Fixpoint(CFGCompactify())).rewrite(mt.code).join(result)
        return result

    @classmethod
    def inline_heuristic(cls, node: ir.Statement) -> bool:
        """The heuristic to decide whether to inline a function call or not.
        inside loops and if-else, only inline simple functions, i.e.
        functions with a single block
        """
        if not isinstance(node.parent_stmt, (scf.For, scf.IfElse)):
            return True  # always inline calls outside of loops and if-else

        if (trait := node.get_trait(ir.CallableStmtInterface)) is None:
            return False  # not a callable, don't inline to be safe
        region = trait.get_callable_region(node)
        return len(region.blocks) == 1

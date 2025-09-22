from dataclasses import dataclass, field

from kirin import ir
from kirin.dialects import ilist, scf
from kirin.ir.method import Method
from kirin.passes import HintConst, Pass, TypeInfer
from kirin.passes.aggressive import UnrollScf
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
class Fold(Pass):
    hint_const: HintConst = field(init=False)

    def __post_init__(self):
        self.hint_const = HintConst(self.dialects, no_raise=self.no_raise)

    def unsafe_run(self, mt: Method) -> RewriteResult:
        result = RewriteResult()
        result = self.hint_const.unsafe_run(mt).join(result)
        rule = Chain(
            ConstantFold(),
            Call2Invoke(),
            InlineGetField(),
            InlineGetItem(),
            ilist.rewrite.InlineGetItem(),
            ilist.rewrite.HintLen(),
            DeadCodeElimination(),
            CommonSubexpressionElimination(),
        )
        result = Fixpoint(Walk(rule)).rewrite(mt.code).join(result)

        return result


@dataclass
class AggressiveUnroll(Pass):
    """Fold pass to fold control flow"""

    fold: Fold = field(init=False)
    typeinfer: TypeInfer = field(init=False)
    scf_unroll: UnrollScf = field(init=False)

    def __post_init__(self):
        self.fold = Fold(self.dialects, no_raise=self.no_raise)
        self.typeinfer = TypeInfer(self.dialects, no_raise=self.no_raise)
        self.scf_unroll = UnrollScf(self.dialects, no_raise=self.no_raise)

    def unsafe_run(self, mt: Method) -> RewriteResult:
        result = RewriteResult()
        result = self.scf_unroll.unsafe_run(mt).join(result)
        result = (
            Walk(Chain(ilist.rewrite.ConstList2IList(), ilist.rewrite.Unroll()))
            .rewrite(mt.code)
            .join(result)
        )
        result = self.typeinfer.unsafe_run(mt).join(result)
        result = self.fold.unsafe_run(mt).join(result)
        result = Walk(Inline(self.inline_heuristic)).rewrite(mt.code).join(result)
        result = Walk(Fixpoint(CFGCompactify())).rewrite(mt.code).join(result)
        return result

    @classmethod
    def inline_heuristic(cls, node: ir.Statement) -> bool:
        """The heuristic to decide whether to inline a function call or not.
        inside loops and if-else, only inline simple functions, i.e.
        functions with a single block
        """
        return not isinstance(
            node.parent_stmt, (scf.For, scf.IfElse)
        )  # always inline calls outside of loops and if-else

from kirin import ir
from kirin.passes import Pass
from kirin.rewrite import (
    Chain,
    CommonSubexpressionElimination,
    DeadCodeElimination,
    Fixpoint,
    Walk,
)

from bloqade.shuttle.rewrite.schedule2path import (
    Canonicalize,
    RewriteAutoInvoke,
    RewriteDeviceCall,
    RewriteScheduleRegion,
)


class ScheduleToPath(Pass):
    """Pass to convert schedule dialect to path dialect."""

    def unsafe_run(self, mt: ir.Method):
        result = Fixpoint(Walk(Canonicalize())).rewrite(mt.code)
        result = (
            Walk(Chain(RewriteAutoInvoke(), RewriteDeviceCall()))
            .rewrite(mt.code)
            .join(result)
        )
        result = Walk(RewriteScheduleRegion()).rewrite(mt.code).join(result)
        result = (
            Fixpoint(
                Walk(Chain(CommonSubexpressionElimination(), DeadCodeElimination()))
            )
            .rewrite(mt.code)
            .join(result)
        )

        return result

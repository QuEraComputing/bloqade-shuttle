from dataclasses import dataclass

from kirin import ir
from kirin.passes import Pass
from kirin.rewrite import Walk
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle import spec
from bloqade.shuttle.analysis.zone import Zone, ZoneAnalysis


@dataclass
class ZoneHintRewrite(RewriteRule):
    analysis_results: dict[ir.SSAValue, Zone]

    def rewrite_Statement(self, node: ir.Statement) -> RewriteResult:
        has_done_something = False
        for result in node.results:
            if has_done_something := result in self.analysis_results:
                result.hints["zone.analysis"] = self.analysis_results[result]

        return RewriteResult(has_done_something=has_done_something)


@dataclass
class HintZone(Pass):
    """
    This pass adds zone hints to SSA values based on the analysis results.
    """

    arch_spec: spec.ArchSpec

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        analysis_frame, _ = ZoneAnalysis(
            mt.dialects, arch_spec=self.arch_spec
        ).run_analysis(mt)
        return Walk(ZoneHintRewrite(analysis_frame.entries)).rewrite(mt.code)

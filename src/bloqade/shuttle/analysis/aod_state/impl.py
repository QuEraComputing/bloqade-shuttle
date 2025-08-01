from kirin import interp
from kirin.analysis.forward import ForwardFrame
from kirin.dialects import scf

from .analysis import AODStateAnalysis
from .lattice import AODState, PythonRuntime


class ScfMethods(scf.absint.Methods):

    @interp.impl(scf.IfElse)
    def if_else(
        self, _interp: AODStateAnalysis, frame: ForwardFrame[AODState], stmt: scf.IfElse
    ):
        cond = frame.get(stmt.cond)

        if isinstance(cond, PythonRuntime):
            if cond.value:
                with _interp.new_frame(stmt, has_parent_access=True) as new_frame:
                    return _interp.run_ssacfg_region(
                        new_frame, stmt.then_body, (PythonRuntime(True),)
                    )
            else:
                with _interp.new_frame(stmt, has_parent_access=True) as new_frame:
                    return _interp.run_ssacfg_region(
                        new_frame, stmt.else_body, (PythonRuntime(False),)
                    )

        else:
            super().if_else(_interp, frame, stmt)

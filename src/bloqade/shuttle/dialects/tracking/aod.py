# from kirin.analysis import ForwardFrame
# from kirin import interp
# from bloqade.shuttle.analysis import aod
# from ._dialect import dialect
# from .stmts import Play, GlobalR, GlobalRz, LocalR, LocalRz, Measure, Fill

# from ..path import Path

# @dialect.register(key="aod.analysis")
# class TrackingMethods(interp.MethodTable):

#     @interp.impl(Play)
#     def play(self, _interp: aod.AODAnalysis, frame: ForwardFrame[aod.AODState], stmt: Play):

#         state = frame.get(stmt.state)
#         if not isinstance(state, aod.AOD):
#             return (state,)

#         path = _interp.get_const_value(Path, stmt.path)
#         for action in path.path:
#             match

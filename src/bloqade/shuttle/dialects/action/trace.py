from bloqade.geometry.dialects import grid
from kirin.interp import Frame, InterpreterError, MethodTable, impl

from bloqade.shuttle.codegen import taskgen

from . import stmts
from ._dialect import dialect


@dialect.register(key="action.tracer")
class ActionTracer(MethodTable):

    intensity_actions = {
        stmts.TurnOnXY: taskgen.TurnOnXYAction,
        stmts.TurnOffXY: taskgen.TurnOffXYAction,
        stmts.TurnOnXSlice: taskgen.TurnOnXSliceAction,
        stmts.TurnOffXSlice: taskgen.TurnOffXSliceAction,
        stmts.TurnOnYSlice: taskgen.TurnOnYSliceAction,
        stmts.TurnOffYSlice: taskgen.TurnOffYSliceAction,
        stmts.TurnOnXYSlice: taskgen.TurnOnXYSliceAction,
        stmts.TurnOffXYSlice: taskgen.TurnOffXYSliceAction,
    }

    @impl(stmts.TurnOnXY)
    @impl(stmts.TurnOffXY)
    @impl(stmts.TurnOnXSlice)
    @impl(stmts.TurnOffXSlice)
    @impl(stmts.TurnOnYSlice)
    @impl(stmts.TurnOffYSlice)
    @impl(stmts.TurnOnXYSlice)
    @impl(stmts.TurnOffXYSlice)
    def construct_intensity_actions(
        self,
        interp: taskgen.TraceInterpreter,
        frame: Frame,
        stmt: stmts.IntensityStatement,
    ):
        if interp.curr_pos is None:
            raise InterpreterError(
                "Position of AOD not set before turning on/off tones"
            )

        x_tone_indices = frame.get(stmt.x_tones)
        y_tone_indices = frame.get(stmt.y_tones)

        interp.trace.append(
            self.intensity_actions[type(stmt)](
                x_tone_indices if isinstance(x_tone_indices, slice) else x_tone_indices,
                y_tone_indices if isinstance(y_tone_indices, slice) else y_tone_indices,
            )
        )
        interp.trace.append(taskgen.WayPointsAction(way_points=[interp.curr_pos]))
        return ()

    @impl(stmts.Move)
    def move(self, interp: taskgen.TraceInterpreter, frame: Frame, stmt: stmts.Move):
        if interp.curr_pos is None:
            raise InterpreterError("Position of AOD not set before moving tones")

        assert isinstance(interp.trace[-1], taskgen.WayPointsAction)

        interp.trace[-1].add_waypoint(pos := frame.get_typed(stmt.grid, grid.Grid))
        if interp.curr_pos.shape != pos.shape:
            raise InterpreterError(
                f"Position of AOD {interp.curr_pos} and target position {pos} have different shapes"
            )
        interp.curr_pos = pos

        return ()

    @impl(stmts.Set)
    def set(self, interp: taskgen.TraceInterpreter, frame: Frame, stmt: stmts.Set):
        pos = frame.get_typed(stmt.grid, grid.Grid)
        interp.trace.append(taskgen.WayPointsAction([pos]))

        interp.curr_pos = pos

        return ()

from dataclasses import dataclass, field
from typing import Any, cast

from bloqade.geometry.dialects import grid
from bloqade.insight.dialects import trajectory
from bloqade.insight.prelude import insight
from bloqade.squin import qubit
from kirin import ir, rewrite
from kirin.analysis import const
from kirin.dialects import cf, ilist, py
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle import arch
from bloqade.shuttle.codegen import taskgen
from bloqade.shuttle.dialects import init, path
from bloqade.shuttle.passes import fold, inject_spec


@insight
def fill(fill_arguments: ilist.IList[grid.Grid, Any]) -> trajectory.AtomState:
    locations = []
    for zone in fill_arguments:
        for x in grid.get_xpos(zone):
            for y in grid.get_ypos(zone):
                locations = locations + [(x, y)]

    return trajectory.initialize(qubit.new(len(locations)), locations)


@dataclass
class ShuttleToInsightRule(RewriteRule):
    fill_state: ir.SSAValue | None = field(default=None, init=False)

    STMTS = (
        cf.Branch,
        cf.ConditionalBranch,
        path.Play,
        init.Fill,
    )

    @staticmethod
    def path_to_trajectory(path: path.Path) -> list[trajectory.Trajectory] | None:
        active_x_indices: set[int] = set()
        active_y_indices: set[int] = set()

        x_indices = range(len(path.x_tones))
        y_indices = range(len(path.y_tones))

        trajectories = []
        for action in path.path:
            match action:
                case taskgen.WayPointsAction(waypoints) if (
                    len(waypoints) > 1
                    and len(active_x_indices) > 0
                    and len(active_y_indices) > 0
                ):
                    # do not add trajectory if no traps are generated,
                    # e.g. the number of active tones are zero for either x or y.
                    active_waypoints = tuple(
                        waypoint.get_view(
                            ilist.IList(sorted(active_x_indices)),
                            ilist.IList(sorted(active_y_indices)),
                        )
                        for waypoint in waypoints
                    )
                    trajectories.append(trajectory.Trajectory(active_waypoints))
                case taskgen.TurnOnAction(x_slice, y_slice):
                    active_x_indices.update(
                        x_indices[x_slice] if isinstance(x_slice, slice) else x_slice
                    )
                    active_y_indices.update(
                        y_indices[y_slice] if isinstance(y_slice, slice) else y_slice
                    )
                case taskgen.TurnOffAction(x_slice, y_slice):
                    active_x_indices.difference_update(
                        x_indices[x_slice] if isinstance(x_slice, slice) else x_slice
                    )
                    active_y_indices.difference_update(
                        y_indices[y_slice] if isinstance(y_slice, slice) else y_slice
                    )
                case _:
                    return None

        return trajectories

    def rewrite_Block(self, node: ir.Block) -> RewriteResult:
        if (
            not isinstance(region := node.parent_node, ir.Region)
            or region._block_idx[node] == 0
        ):
            # skip entry block of entry method
            return RewriteResult()

        self.curr_state = node.args.insert_from(
            0, trajectory.AtomStateType, name="atom_state"
        )
        return RewriteResult(has_done_something=True)

    def rewrite_Statement(self, node: Statement) -> RewriteResult:
        if not isinstance(node, self.STMTS):
            return RewriteResult()

        return getattr(self, f"rewrite_{type(node).__name__}", self.default)(node)

    def default(self, node: Statement) -> RewriteResult:
        return RewriteResult()

    def rewrite_Fill(self, node: Statement) -> RewriteResult:
        if (
            self.fill_state is None
            or not isinstance(node, init.Fill)
            or not isinstance(
                locations_hint := node.locations.hints.get("const"), const.Value
            )
            or not isinstance(locations := locations_hint.data, ilist.IList)
            or (parent_block := node.parent_block) is None
        ):
            return RewriteResult()

        flattened_locations = []
        for location in locations:
            if not isinstance(location, grid.Grid):
                return RewriteResult()
            for x in grid.get_xpos(location):
                for y in grid.get_ypos(location):
                    flattened_locations.append((x, y))

        # split current block into two blocks, one with the fill statement and one without
        new_block = ir.Block()

        while (arg := parent_block.args.popfirst()) is not None:
            new_block.args.append(arg)

        stmt = parent_block.first_stmt
        while stmt is not node and stmt is not None:
            next_stmt = stmt.next_stmt
            stmt.detach()
            new_block.stmts.append(stmt)
            stmt = next_stmt

        if len(parent_block.stmts) == 0:
            return RewriteResult()

        # replace the fill statement with a constant that initializes the atom state
        new_block.stmts.append(num_qubits := py.Constant(len(flattened_locations)))
        new_block.stmts.append(locations_stmt := py.Constant(flattened_locations))
        new_block.stmts.append(qubits := qubit.New(num_qubits.result))
        new_block.stmts.append(
            curr_state_stmt := trajectory.Initialize(
                qubits.result, locations_stmt.result
            )
        )

        self.curr_state = curr_state_stmt.state
        new_block.stmts.append(
            cf.Branch(arguments=(self.curr_state,), successor=parent_block)
        )

        return RewriteResult(has_done_something=True)

    def rewrite_Play(self, node: path.Play) -> RewriteResult:
        if node.path.type.is_subseteq(path.ParallelPathType):
            return RewriteResult()

        path_value = node.path.hints.get("const")

        if not isinstance(path_value, const.Value):
            return RewriteResult()

        trajectories = self.path_to_trajectory(cast(path.Path, path_value.data))

        if trajectories is None:
            return RewriteResult()

        for traj in trajectories:
            (traj_stmt := py.Constant(traj)).insert_before(node)
            (
                move_stmt := trajectory.Move(self.curr_state, traj_stmt.result)
            ).insert_before(node)
            self.curr_state = move_stmt.result

        node.delete()

        return RewriteResult(has_done_something=True)

    def rewrite_Branch(self, node: cf.Branch) -> RewriteResult:
        node.replace_by(
            cf.Branch(
                arguments=(self.curr_state, *node.arguments),
                successor=node.successor,
            )
        )
        return RewriteResult(has_done_something=True)

    def rewrite_ConditionalBranch(self, node: cf.ConditionalBranch) -> RewriteResult:
        node.replace_by(
            cf.ConditionalBranch(
                node.cond,
                (self.curr_state, *node.then_arguments),
                (self.curr_state, *node.else_arguments),
                then_successor=node.then_successor,
                else_successor=node.else_successor,
            )
        )
        return RewriteResult(has_done_something=True)


@dataclass
class PathToInsight(Pass):
    arch_spec: arch.ArchSpec

    def unsafe_run(self, mt: ir.Method) -> RewriteResult:
        result = inject_spec.InjectSpecsPass(
            mt.dialects, self.arch_spec, fold=False
        ).unsafe_run(mt)
        result = result.join(
            fold.AggressiveUnroll(mt.dialects, no_raise=self.no_raise).unsafe_run(mt)
        )
        result = result.join(rewrite.Walk(ShuttleToInsightRule()).rewrite(mt.code))
        return result

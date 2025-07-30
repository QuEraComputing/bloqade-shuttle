from dataclasses import dataclass, field
from typing import Any, cast

from bloqade.geometry.dialects import grid
from bloqade.insight.dialects import trajectory
from bloqade.squin import qubit
from kirin import ir, rewrite
from kirin.analysis import const
from kirin.dialects import cf, ilist, py
from kirin.ir.nodes.stmt import Statement
from kirin.passes import Pass
from kirin.rewrite.abc import RewriteResult, RewriteRule

from bloqade.shuttle import arch
from bloqade.shuttle.codegen import taskgen
from bloqade.shuttle.dialects import gate, init, path
from bloqade.shuttle.passes import fold, inject_spec


@dataclass
class PathToInsightRule(RewriteRule):
    fill_state: ir.SSAValue | None = field(default=None, init=False)

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
        return getattr(self, f"rewrite_{type(node).__name__}", self.default)(node)

    def default(self, node: Statement) -> RewriteResult:
        return RewriteResult()

    def rewrite_Fill(self, node: init.Fill) -> RewriteResult:
        if (
            self.fill_state is not None
            or not isinstance(
                locations_hint := node.locations.hints.get("const"), const.Value
            )
            or (parent_block := node.parent_block) is None
            or (parent_region := parent_block.parent_node) is None
        ):
            return RewriteResult()

        block_idx = parent_region._block_idx[parent_block]
        parent_region.blocks.insert(block_idx, new_block := ir.Block())

        for arg in parent_block.args:
            new_block.args.append_from(arg.type, name=arg.name)

        for old_arg, new_arg in zip(list(parent_block.args), new_block.args):
            old_arg.replace_by(new_arg)
            parent_block.args.delete(old_arg)

        parent_block.args.append_from(trajectory.AtomStateType, name="atom_state")

        # split the statements of the parent block
        stmt = parent_block.first_stmt
        while stmt is not node and stmt is not None:
            next_stmt = stmt.next_stmt
            stmt.detach()
            new_block.stmts.append(stmt)
            stmt = next_stmt

        if len(parent_block.stmts) == 0:
            return RewriteResult()

        # replace the fill statement with a constant that initializes the atom state
        location = cast(ilist.IList[grid.Grid[Any, Any], Any], locations_hint.data)
        flattened_locations = []
        for location in location:
            for x in location.x_positions:
                for y in location.y_positions:
                    flattened_locations.append((x, y))

        new_block.stmts.append(num_qubits := py.Constant(len(flattened_locations)))
        new_block.stmts.append(qubits := qubit.New(num_qubits.result))
        new_block.stmts.append(
            locations_stmt := py.Constant(ilist.IList(flattened_locations))
        )
        new_block.stmts.append(
            curr_state_stmt := trajectory.Initialize(
                qubits.result, locations_stmt.result
            )
        )

        self.curr_state = curr_state_stmt.state
        new_block.stmts.append(
            cf.Branch(arguments=(self.curr_state,), successor=parent_block)
        )
        node.delete()

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

    def rewrite_TopHatCZ(self, node: gate.TopHatCZ) -> RewriteResult:
        if not isinstance(zone_value := node.zone.hints.get("const"), const.Value):
            return RewriteResult()

        zone = cast(grid.Grid, zone_value.data)
        ymin, ymax = zone.y_bounds()
        assert ymin is not None and ymax is not None, "Zone must have y bounds"
        ymin_keepout = ymin - node.lower_buffer
        ymax_keepout = ymax + node.upper_buffer

        (ymin_stmt := py.Constant(ymin)).insert_before(node)
        (ymax_stmt := py.Constant(ymax)).insert_before(node)
        (ymin_keepout_stmt := py.Constant(ymin_keepout)).insert_before(node)
        (ymax_keepout_stmt := py.Constant(ymax_keepout)).insert_before(node)

        node.replace_by(
            cz_stmt := trajectory.CZTopHat(
                self.curr_state,
                ymin=ymin_stmt.result,
                ymax=ymax_stmt.result,
                ymin_keepout=ymin_keepout_stmt.result,
                ymax_keepout=ymax_keepout_stmt.result,
            )
        )

        self.curr_state = cz_stmt.result

        return RewriteResult(has_done_something=True)

    def rewrite_GlobalR(self, node: gate.GlobalR) -> RewriteResult:
        node.replace_by(
            gate_stmt := trajectory.GlobalR(
                self.curr_state,
                axes_angle=node.axis_angle,
                rotation_angle=node.rotation_angle,
            )
        )
        self.curr_state = gate_stmt.result

        return RewriteResult(has_done_something=True)

    def rewrite_GlobalRz(self, node: gate.GlobalRz) -> RewriteResult:
        node.replace_by(
            gate_stmt := trajectory.GlobalRz(
                self.curr_state,
                rotation_angle=node.rotation_angle,
            )
        )
        self.curr_state = gate_stmt.result

        return RewriteResult(has_done_something=True)

    def rewrite_LocalR(self, node: gate.LocalR) -> RewriteResult:
        node.replace_by(
            gate_stmt := trajectory.LocalR(
                self.curr_state,
                axes_angle=node.axis_angle,
                rotation_angle=node.rotation_angle,
                locations=node.zone,
            )
        )
        self.curr_state = gate_stmt.result

        return RewriteResult(has_done_something=True)

    def rewrite_LocalRz(self, node: gate.LocalRz) -> RewriteResult:
        node.replace_by(
            gate_stmt := trajectory.LocalRz(
                self.curr_state,
                rotation_angle=node.rotation_angle,
                locations=node.zone,
            )
        )
        self.curr_state = gate_stmt.result

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
        result = result.join(rewrite.Walk(PathToInsightRule()).rewrite(mt.code))
        return result

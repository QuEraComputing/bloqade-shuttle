from dataclasses import dataclass

from kirin import ir
from kirin.dialects import ilist, py
from kirin.rewrite import abc

from bloqade.shuttle.analysis.schedule.lattice import AutoSchedule, ScheduleLattice
from bloqade.shuttle.dialects import path, schedule


@dataclass
class AutoRewriter(abc.RewriteRule):

    groups: dict[ir.SSAValue, ScheduleLattice]

    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if not isinstance(node, path.Play) or not isinstance(
            (auto_stmt := node.path.owner), path.Auto
        ):
            return abc.RewriteResult()

        if auto_stmt.result not in self.groups:
            return abc.RewriteResult()

        auto_group = self.groups.get(auto_stmt.result)

        if not isinstance(auto_group, AutoSchedule):
            return abc.RewriteResult()

        play_groups = {}
        for group_id, tones, pth in zip(
            auto_group.group_id, auto_group.tones, auto_stmt.paths
        ):
            play_groups.setdefault(group_id, []).append((tones, pth))

        for group_id in sorted(play_groups.keys()):
            paths = play_groups[group_id]
            new_paths = []

            for tones, pth in paths:
                if isinstance((gen := pth.owner), path.Gen) and isinstance(
                    (move_fn_stmt := gen.device_task.owner), schedule.NewTweezerTask
                ):
                    (x_tones := py.Constant(ilist.IList(tones.x_tones))).insert_before(
                        node
                    )
                    (y_tones := py.Constant(ilist.IList(tones.y_tones))).insert_before(
                        node
                    )
                    (
                        new_device_fn := schedule.NewDeviceFunction(
                            move_fn=move_fn_stmt.move_fn,
                            x_tones=x_tones.result,
                            y_tones=y_tones.result,
                        )
                    ).insert_before(node)
                    (
                        new_gen := path.Gen(
                            new_device_fn.result, gen.inputs, kwargs=gen.kwargs
                        )
                    ).insert_before(node)
                    new_paths.append(new_gen.result)
                else:
                    new_paths.append(pth)

            if len(new_paths) > 1:
                (new_parallel := path.Parallel(tuple(new_paths))).insert_before(node)
                path.Play(new_parallel.result).insert_before(node)

        node.delete()

        # Remove the original node
        node.delete()

        return abc.RewriteResult(has_done_something=True)

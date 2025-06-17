from kirin import ir
from kirin.dialects import func, py
from kirin.rewrite import abc

from bloqade.shuttle.dialects import path, schedule


class RewriteDeviceCall(abc.RewriteRule):
    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if not isinstance(node, func.Call) or not node.callee.type.is_subseteq(
            schedule.DeviceFunctionType
        ):
            return abc.RewriteResult()

        (
            path_gen := path.Gen(node.callee, node.inputs, kwargs=node.kwargs)
        ).insert_before(node)

        if not isinstance(node.parent_stmt, (schedule.Auto, schedule.Parallel)):
            node.replace_by(path.Play(path_gen.result))
        else:
            node.delete()

        return abc.RewriteResult(has_done_something=True)


class RewriteAutoInvoke(abc.RewriteRule):
    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if not isinstance(node.parent_stmt, schedule.Auto):
            return abc.RewriteResult()

        if isinstance(node, func.Invoke):
            (callee_stmt := py.Constant(node.callee)).insert_before(node)
            callee_ssa = callee_stmt.result
        elif isinstance(node, func.Call):
            callee_ssa = node.callee
        else:
            return abc.RewriteResult()

        (tweezer_task := schedule.NewTweezerTask(move_fn=callee_ssa)).insert_before(
            node
        )
        (path.Gen(tweezer_task.result, node.inputs, kwargs=node.kwargs)).insert_before(
            node
        )

        node.delete()

        return abc.RewriteResult(has_done_something=True)


class RewriteScheduleRegion(abc.RewriteRule):
    CLASSES = {
        schedule.Auto: path.Auto,
        schedule.Parallel: path.Parallel,
    }

    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if not isinstance(node, schedule.ExecutableRegion):
            return abc.RewriteResult()

        new_node_type = self.CLASSES[type(node)]
        assert isinstance(node, schedule.ExecutableRegion)
        paths = []

        for stmt in node.body.walk():
            stmt.detach()
            stmt.insert_before(node)
            stmt_result = stmt.expect_one_result()
            if len(stmt_result.uses) == 0:
                # this is required for nested regions where a previously
                # lifted region might have used this current SSA value.
                paths.append(stmt_result)

        (parallel := new_node_type(tuple(paths))).insert_before(node)

        if not isinstance(node.parent_stmt, schedule.ExecutableRegion):
            # If the parent is not a parallel or auto region, we need to wrap it in a Play statement
            # to ensure it can be executed.
            node.replace_by(stmt=path.Play(parallel.result))
        else:
            # If the parent is already a parallel or auto region, we can just replace the node.
            node.delete()

        return abc.RewriteResult(has_done_something=True)


class Canonicalize(abc.RewriteRule):
    """Flatten nested parallel regions into a single parallel region."""

    CLASSES = (schedule.Auto, schedule.Parallel)

    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if (node_type := type(node)) not in self.CLASSES or not isinstance(
            node.parent_stmt, node_type
        ):
            return abc.RewriteResult()

        assert isinstance(node, self.CLASSES)

        detached_stmts = [
            stmt for stmt in node.body.walk() if not isinstance(stmt, node_type)
        ]
        has_done_something = False
        for stmt in detached_stmts:
            stmt.detach()
            stmt.insert_before(node)
            has_done_something = True

        if len(node.body.blocks[0].stmts) == 0:
            # If the body is empty, we can remove the node
            has_done_something = True
            node.delete()

        return abc.RewriteResult(has_done_something=has_done_something)

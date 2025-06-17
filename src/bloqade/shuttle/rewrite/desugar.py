from kirin import ir, types
from kirin.rewrite import abc

from bloqade.shuttle.dialects import action


class DesugarTurnOnRewrite(abc.RewriteRule):

    @staticmethod
    def get_stmt_type(is_x_slice: bool, is_y_slice: bool):
        if is_x_slice and is_y_slice:
            return action.TurnOnXYSlice
        elif is_x_slice:
            return action.TurnOnXSlice
        elif is_y_slice:
            return action.TurnOnYSlice
        else:
            return action.TurnOnXY

    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if isinstance(node, action.TurnOn):
            is_x_slice = node.x_tones.type.is_subseteq(types.Slice)
            is_y_slice = node.y_tones.type.is_subseteq(types.Slice)
            stmt_type = self.get_stmt_type(is_x_slice, is_y_slice)
            node.replace_by(stmt_type(x_tones=node.x_tones, y_tones=node.y_tones))
            return abc.RewriteResult(has_done_something=True)

        return abc.RewriteResult()


class DesugarTurnOffRewrite(abc.RewriteRule):
    @staticmethod
    def get_stmt_type(is_x_slice: bool, is_y_slice: bool):
        if is_x_slice and is_y_slice:
            return action.TurnOffXYSlice
        elif is_x_slice:
            return action.TurnOffXSlice
        elif is_y_slice:
            return action.TurnOffYSlice
        else:
            return action.TurnOffXY

    def rewrite_Statement(self, node: ir.Statement) -> abc.RewriteResult:
        if isinstance(node, action.TurnOff):
            is_x_slice = node.x_tones.type.is_subseteq(types.Slice)
            is_y_slice = node.y_tones.type.is_subseteq(types.Slice)
            stmt_type = self.get_stmt_type(is_x_slice, is_y_slice)
            node.replace_by(stmt_type(x_tones=node.x_tones, y_tones=node.y_tones))
            return abc.RewriteResult(has_done_something=True)

        return abc.RewriteResult()

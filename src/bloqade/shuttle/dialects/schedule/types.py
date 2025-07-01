import typing

from kirin import types

Param = typing.ParamSpec("Param")


class Task(typing.Generic[Param]):
    def __call__(self, *args: Param.args, **kwargs: Param.kwargs) -> None:
        raise NotImplementedError("This method should not be called directly.")


TaskType = types.PyClass(Task)

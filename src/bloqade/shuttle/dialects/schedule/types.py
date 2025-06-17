import typing
from dataclasses import dataclass

from kirin import ir, types
from kirin.dialects import ilist

Param = typing.ParamSpec("Param")


class AbstractDeviceTask(typing.Generic[Param]):
    def __call__(self, *args: Param.args, **kwargs: Param.kwargs) -> None:
        raise NotImplementedError("This method should not be called directly.")


@dataclass
class DeviceFunction(AbstractDeviceTask[Param]):
    move_fn: ir.Method[Param, None]
    x_tones: ilist.IList[int, typing.Any]
    y_tones: ilist.IList[int, typing.Any]

    def __hash__(self):
        return id(self)


@dataclass
class ReverseDeviceFunction(AbstractDeviceTask[Param]):
    device_task: DeviceFunction[Param]

    def __hash__(self):
        return id(self)


DeviceFunctionType = types.PyClass(AbstractDeviceTask)

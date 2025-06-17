from typing import Any, ContextManager, ParamSpec

from kirin import ir
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import (
    Auto,
    NewDeviceFunction,
    Parallel,
    Reverse,
)
from .types import DeviceFunction, ReverseDeviceFunction

Param = ParamSpec("Param")


@_wraps(NewDeviceFunction)
def device_fn(
    move_fn: ir.Method[Param, None],
    x_tones: list[int] | ilist.IList[int, Any],
    y_tones: list[int] | ilist.IList[int, Any],
) -> DeviceFunction[Param]:
    """Create a device function from a move function.

    Args:
        move_fn (Callable): The move function to be wrapped.
        x_tones (list[int]|): The x tones to be used in the device function.
        y_tones: The y tones to be used in the device function.


    """
    ...


@_wraps(Reverse)
def reverse(
    device_fn: DeviceFunction[Param],
) -> ReverseDeviceFunction[Param]:
    """Create a reverse device function from a device function.

    Args:
        device_fn (DeviceFunction): The device function to be reversed.


    """
    ...


@_wraps(Parallel)
def parallel() -> ContextManager: ...


@_wraps(Auto)
def auto() -> ContextManager: ...

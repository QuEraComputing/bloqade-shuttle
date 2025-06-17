from typing import TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, schedule
from bloqade.shuttle.prelude import move, tweezer

NumX = TypeVar("NumX")
NumY = TypeVar("NumY")
NumWaypoints = TypeVar("NumWaypoints")


@tweezer
def move_by_waypoints_kernel(
    waypoints: ilist.IList[grid.Grid[NumX, NumY], NumWaypoints],
    pick: bool,
    drop: bool,
):
    """Pick up the tweezer at the specified location."""
    action.set_loc(waypoints[0])
    if pick:
        action.turn_on(action.ALL, action.ALL)

    num_waypoints = len(waypoints)
    for i in range(1, num_waypoints):
        action.move(waypoints[i])

    if drop:
        action.turn_off(action.ALL, action.ALL)


@move
def move_by_waypoints(
    waypoints: ilist.IList[grid.Grid[NumX, NumY], NumWaypoints],
    pick: bool = True,
    drop: bool = True,
):
    """Move the tweezer by a list of waypoints.

    Args:
        waypoints (ilist.IList[grid.Grid[NumX, NumY], NumWaypoints]): The waypoints to move to.
        pick (bool): Whether to pick up the tweezer at the first waypoint. Defaults to True.
        drop (bool): Whether to drop the tweezer at the last waypoint. Defaults to True.

    """
    if len(waypoints) < 1:
        return

    shape = grid.shape(waypoints[0])
    device_kernel = schedule.device_fn(
        move_by_waypoints_kernel,
        ilist.range(shape[0]),
        ilist.range(shape[1]),
    )
    device_kernel(waypoints, pick, drop)

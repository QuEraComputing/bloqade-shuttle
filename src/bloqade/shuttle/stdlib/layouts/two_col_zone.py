from itertools import repeat
from typing import TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, schedule, spec
from bloqade.shuttle.prelude import move, tweezer

from .asserts import assert_sorted


def get_spec(
    num_x: int, num_y: int, spacing: float = 10.0, gate_spacing: float = 2.0
) -> spec.ArchSpec:
    """Create a static trap spec with a single zone with pairs of traps oriented
    horizontally.

    Args:
        num_x (int): Number of pairs of traps in the x direction.
        num_y (int): Number of pairs of traps in the y direction.
        spacing (float): Spacing between traps in both directions. Default is 10.0.
        gate_spacing (float): Spacing between gates. Default is 2.0.

    Returns:
        spec.Spec: A specification object containing the layout with a single zone.

    """
    x_spacing = sum(repeat((gate_spacing, spacing), num_x - 1), ()) + (gate_spacing,)
    y_spacing = tuple(repeat(spacing, num_y - 1))

    return spec.ArchSpec(
        layout=spec.Layout(
            {"traps": grid.Grid(x_spacing, y_spacing, 0.0, 0.0)},
            set(["traps"]),
            set(["traps"]),
            set(["traps"]),
        )
    )


NumX = TypeVar("NumX")
NumY = TypeVar("NumY")


@tweezer
def rearrange_impl(
    src_x: ilist.IList[int, NumX],
    src_y: ilist.IList[int, NumY],
    dst_x: ilist.IList[int, NumX],
    dst_y: ilist.IList[int, NumY],
):
    assert len(src_x) == len(
        dst_x
    ), "Source and destination x indices must have the same length."
    assert len(src_y) == len(
        dst_y
    ), "Source and destination y indices must have the same length."

    assert_sorted(src_x)
    assert_sorted(src_y)
    assert_sorted(dst_x)
    assert_sorted(dst_y)

    zone = spec.get_static_trap(zone_id="traps")

    start = grid.sub_grid(zone, src_x, src_y)
    end = grid.sub_grid(zone, dst_x, dst_y)

    def parking_x(index: int):
        x_positions = grid.get_xpos(zone)
        return x_positions[index] + 3.0 * (2 * (index % 2) - 1)

    def parking_y_start(index: int):
        start_y = grid.get_ypos(start)[index]
        end_y = grid.get_ypos(end)[index]
        if start_y <= end_y:
            start_y = start_y + 3.0
        else:
            start_y = start_y - 3.0

        return start_y

    def parking_y_end(index: int):
        start_y = grid.get_ypos(start)[index]
        end_y = grid.get_ypos(end)[index]
        if start_y < end_y:
            end_y = end_y - 3.0
        else:
            end_y = end_y + 3.0

        return end_y

    num_y = len(src_y)

    src_parking = grid.from_positions(
        ilist.map(parking_x, src_x), ilist.map(parking_y_start, ilist.range(num_y))
    )
    dst_parking = grid.from_positions(
        ilist.map(parking_x, dst_x), ilist.map(parking_y_end, ilist.range(num_y))
    )
    mid_pos = grid.from_positions(
        grid.get_xpos(src_parking), grid.get_ypos(dst_parking)
    )

    action.set_loc(start)
    action.turn_on(action.ALL, action.ALL)
    action.move(src_parking)
    action.move(mid_pos)
    action.move(dst_parking)
    action.move(end)
    action.turn_off(action.ALL, action.ALL)


@move
def rearrange(
    src_x: ilist.IList[int, NumX],
    src_y: ilist.IList[int, NumY],
    dst_x: ilist.IList[int, NumX],
    dst_y: ilist.IList[int, NumY],
):
    if len(src_x) < 1 or len(dst_x) < 1:
        return

    x_tones = ilist.range(len(src_x))
    y_tones = ilist.range(len(src_y))

    device_fn = schedule.device_fn(rearrange_impl, x_tones, y_tones)
    device_fn(src_x, src_y, dst_x, dst_y)

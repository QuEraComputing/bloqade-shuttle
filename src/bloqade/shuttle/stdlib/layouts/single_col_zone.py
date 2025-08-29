from itertools import repeat
from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, schedule, spec
from bloqade.shuttle.prelude import move, tweezer

from .asserts import assert_sorted


def get_spec(num_x: int, num_y: int, spacing: float = 10.0) -> spec.ArchSpec:
    """Create a static trap spec with a single zone. compatible with the stdlib

    Args:
        num_x (int): Number of traps in the x direction.
        num_y (int): Number of traps in the y direction.
        spacing (float): Spacing between traps in both directions. Default is 10.0.

    Returns:
        spec.Spec: A specification object containing the layout with a single zone.

    """
    x_spacing = tuple(repeat(spacing, num_x - 1))
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
def single_zone_move_cz(
    zone: grid.Grid[Any, Any],
    ctrl_x_ids: ilist.IList[int, NumX],
    ctrl_y_ids: ilist.IList[int, NumY],
    qarg_x_ids: ilist.IList[int, NumX],
    qarg_y_ids: ilist.IList[int, NumY],
    shift_x: float,
    shift_y: float,
):
    assert len(ctrl_x_ids) == len(
        qarg_x_ids
    ), "Control and target x indices must have the same length."

    assert len(ctrl_y_ids) == len(
        qarg_y_ids
    ), "Control and target y indices must have the same length."

    assert_sorted(ctrl_x_ids)
    assert_sorted(ctrl_y_ids)
    assert_sorted(qarg_x_ids)
    assert_sorted(qarg_y_ids)

    start = grid.sub_grid(zone, ctrl_x_ids, ctrl_y_ids)
    target_atoms = grid.sub_grid(zone, qarg_x_ids, qarg_y_ids)

    end = grid.shift(target_atoms, shift_x, shift_y)
    first_pos = grid.shift(start, shift_x, shift_y)
    second_pos = grid.from_positions(grid.get_xpos(end), grid.get_ypos(first_pos))

    action.set_loc(start)
    action.turn_on(action.ALL, action.ALL)
    action.move(first_pos)
    action.move(second_pos)
    action.move(end)


@move
def default_move_cz_impl(
    zone: grid.Grid[Any, Any],
    x_shift: float,
    y_shift: float,
    ctrl_x_ids: ilist.IList[int, NumX],
    ctrl_y_ids: ilist.IList[int, NumY],
    qarg_x_ids: ilist.IList[int, NumX],
    qarg_y_ids: ilist.IList[int, NumY],
):
    """Move atoms from the start ids and run cz gate with the atoms at the end ids.

    Args:
        zone (grid.Grid[Any, Any]): The grid representing the trap layout (zone) in which atoms are moved.
        x_shift (float): The amount to shift atoms in the x direction during the move.
        y_shift (float): The amount to shift atoms in the y direction during the move.
        ctrl_x_ids (ilist.IList[int, NumX]): The x-indices of the starting positions.
        ctrl_y_ids (ilist.IList[int, NumY]): The y-indices of the starting positions.
        qarg_x_ids (ilist.IList[int, NumX]): The x-indices of the ending positions.
        qarg_y_ids (ilist.IList[int, NumY]): The y-indices of the ending positions.
    """
    if len(ctrl_x_ids) < 1 or len(qarg_x_ids) < 1:
        return

    fwd_kernel = schedule.device_fn(
        single_zone_move_cz,
        ilist.range(len(ctrl_x_ids)),
        ilist.range(len(ctrl_y_ids)),
    )
    bwd_kernel = schedule.reverse(fwd_kernel)

    fwd_kernel(zone, ctrl_x_ids, ctrl_y_ids, qarg_x_ids, qarg_y_ids, x_shift, y_shift)
    gate.top_hat_cz(zone)
    bwd_kernel(zone, qarg_x_ids, qarg_y_ids, ctrl_x_ids, ctrl_y_ids, x_shift, y_shift)


DEFAULT_X_SHIFT = 2.0
DEFAULT_Y_SHIFT = 2.0


@move
def cz_move(
    ctrl_x_ids: ilist.IList[int, NumX],
    ctrl_y_ids: ilist.IList[int, NumY],
    qarg_x_ids: ilist.IList[int, NumX],
    qarg_y_ids: ilist.IList[int, NumY],
):
    zone = spec.get_static_trap(zone_id="traps")
    default_move_cz_impl(
        zone,
        DEFAULT_X_SHIFT,
        DEFAULT_Y_SHIFT,
        ctrl_x_ids,
        ctrl_y_ids,
        qarg_x_ids,
        qarg_y_ids,
    )

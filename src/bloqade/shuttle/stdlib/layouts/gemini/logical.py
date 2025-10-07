from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, schedule, spec, tweezer
from bloqade.shuttle.prelude import move

from ..asserts import assert_sorted
from .base_spec import get_base_spec


def get_spec():
    """Get the architecture specification for the Gemini logical qubit layout.

    Returns:
        ArchSpec: The architecture specification with Gemini logical qubit layout.

    """
    arch_spec = get_base_spec()

    gate_zone = arch_spec.layout.static_traps["gate_zone"]
    aom_sites = arch_spec.layout.special_grid["aom_sites"]
    top_reservoir = arch_spec.layout.static_traps["top_reservoir"]
    bottom_reservoir = arch_spec.layout.static_traps["bottom_reservoir"]

    left_traps = gate_zone[::2, :]
    right_traps = gate_zone[1::2, :]
    S_block = top_reservoir[4 : 4 + 7 * 4, 8 : 8 + 5 * 2 : 2]
    M_block = bottom_reservoir[4 : 4 + 7 * 4 :, 2 : 2 + 5 * 2 : 2]

    S0_block = S_block[: 2 * 7, :]
    S1_block = S_block[2 * 7 :, :]
    M0_block = M_block[: 2 * 7, :]
    M1_block = M_block[2 * 7 :, :]

    SL0_block = S0_block[::2, :]
    SR0_block = S0_block[1::2, :]

    SL1_block = S1_block[::2, :]
    SR1_block = S1_block[1::2, :]

    ML0_block = M0_block[::2, :]
    MR0_block = M0_block[1::2, :]
    ML1_block = M1_block[::2, :]
    MR1_block = M1_block[1::2, :]

    GL_blocks = left_traps[2 : 2 + 2 * 7, :]
    GR_blocks = right_traps[2 : 2 + 2 * 7, :]

    GL0_block = GL_blocks[:7, :]
    GR0_block = GR_blocks[:7, :]

    GL1_block = GL_blocks[7 : 2 * 7, :]
    GR1_block = GR_blocks[7 : 2 * 7, :]

    AOM0_block = aom_sites[2 : 2 + 7, :]
    AOM1_block = aom_sites[2 + 7 : 2 + 7 + 7, :]

    additional_static_traps = {
        "left_gate_zone_sites": left_traps,
        "right_gate_zone_sites": right_traps,
        "top_reservoir_sites": top_reservoir,
        "bottom_reservoir_sites": bottom_reservoir,
        "GL_blocks": GL_blocks,
        "GR_blocks": GR_blocks,
        "GL0_block": GL0_block,
        "GL1_block": GL1_block,
        "GR0_block": GR0_block,
        "GR1_block": GR1_block,
        "SL0_block": SL0_block,
        "SL1_block": SL1_block,
        "SR0_block": SR0_block,
        "SR1_block": SR1_block,
        "ML0_block": ML0_block,
        "ML1_block": ML1_block,
        "MR0_block": MR0_block,
        "MR1_block": MR1_block,
    }
    additional_special_grids = {
        "AOM0_block": AOM0_block,
        "AOM1_block": AOM1_block,
    }

    arch_spec.layout.static_traps.update(additional_static_traps)
    arch_spec.layout.special_grid.update(additional_special_grids)
    arch_spec.layout.has_cz.add("gate_zone")
    arch_spec.layout.fillable.update(("GL0_block", "GL1_block"))
    arch_spec.layout.has_local.update(
        ("GL0_block", "GL1_block", "GR0_block", "GR1_block")
    )

    logical_rows, _ = SL0_block.shape
    logical_cols = 2
    code_size = 7

    int_constants = {
        "logical_rows": logical_rows,
        "logical_cols": logical_cols,
        "code_size": code_size,
    }

    arch_spec.int_constants.update(int_constants)

    return arch_spec


N = TypeVar("N")


@tweezer
def get_block(
    block_id: str,
    col_indices: ilist.IList[int, Any],
    row_indices: ilist.IList[int, Any],
):
    """Returns the zone corresponding to the specified block and column.

    Args:
        block_id (str): The block identifier, either "GL" or "GR".
        col_id (int): The column identifier, either 0 or 1.

    Returns:
        Grid: The grid corresponding to the specified block and column.

    """
    assert block_id in ("GL", "GR"), "block_id must be either 'GL' or 'GR'"

    block = None
    if block_id == "GL":
        block = spec.get_static_trap(zone_id="GL_blocks")
    elif block_id == "GR":
        block = spec.get_static_trap(zone_id="GR_blocks")

    code_size = spec.get_int_constant(constant_id="code_size")

    def _get_physical_columns(logical_col: int):
        return ilist.range(logical_col * code_size, (logical_col + 1) * code_size)

    def join(
        lhs: ilist.IList[int, Any], rhs: ilist.IList[int, Any]
    ) -> ilist.IList[int, Any]:
        return lhs + rhs

    physical_columns_lists = ilist.map(_get_physical_columns, col_indices)
    physical_col_indices = ilist.foldl(
        join, physical_columns_lists[1:], physical_columns_lists[0]
    )

    return block[physical_col_indices, row_indices]


@tweezer
def get_other_block(block_id: str) -> str:
    assert block_id in ("GL", "GR"), "block_id must be either 'GL' or 'GR'"
    other_block = "GL"
    if block_id == "GL":
        other_block = "GR"
    return other_block


@tweezer
def swap_block_impl(
    src_block: str,
    selected_cols: ilist.IList[int, Any],
    selected_rows: ilist.IList[int, Any],
):

    assert_sorted(selected_cols)
    assert_sorted(selected_rows)

    dst_block = get_other_block(src_block)

    start = get_block(src_block, selected_cols, selected_rows)
    end = get_block(dst_block, selected_cols, selected_rows)

    action.set_loc(start)
    action.turn_on(action.ALL, action.ALL)
    action.move(end)
    action.turn_off(action.ALL, action.ALL)


@tweezer
def vertical_move_impl(
    block_id: str,
    col_indices: ilist.IList[int, Any],
    src_rows: ilist.IList[int, N],
    dst_rows: ilist.IList[int, N],
):
    assert_sorted(col_indices)
    assert_sorted(src_rows)
    assert_sorted(dst_rows)

    assert len(src_rows) == len(
        dst_rows
    ), "src_rows and dst_rows must have the same length"

    assert block_id in ("GL", "GR"), "block_id must be either 'GL' or 'GR'"
    src = get_block(block_id, col_indices, src_rows)
    dst = get_block(block_id, col_indices, dst_rows)

    x_shift = spec.get_float_constant(constant_id="col_separation") / 2.0
    if block_id == "GL":
        x_shift = -x_shift

    action.set_loc(src)
    action.turn_on(action.ALL, action.ALL)
    action.move(grid.shift(src, x_shift, 0.0))
    action.move(grid.shift(dst, x_shift, 0.0))
    action.move(dst)
    action.turn_off(action.ALL, action.ALL)


@tweezer
def horizontal_move_impl(
    block_id: str,
    row_indices: ilist.IList[int, Any],
    src_cols: ilist.IList[int, N],
    dst_cols: ilist.IList[int, N],
):
    assert_sorted(row_indices)
    assert_sorted(src_cols)
    assert_sorted(dst_cols)

    assert len(src_cols) == len(
        dst_cols
    ), "src_cols and dst_cols must have the same length"

    assert block_id in ("GL", "GR"), "block_id must be either 'GL' or 'GR'"
    src = get_block(block_id, src_cols, row_indices)
    dst = get_block(block_id, dst_cols, row_indices)
    y_shift = spec.get_float_constant(constant_id="row_separation") / 2.0

    action.set_loc(src)
    action.turn_on(action.ALL, action.ALL)
    action.move(grid.shift(src, 0.0, y_shift))
    action.move(grid.shift(dst, 0.0, y_shift))
    action.move(dst)
    action.turn_off(action.ALL, action.ALL)


Nx = TypeVar("Nx", bound=int)
Ny = TypeVar("Ny", bound=int)


@move
def entangle(
    src_block: str,
    src_cols: ilist.IList[int, Nx],
    src_rows: ilist.IList[int, Ny],
    dst_block: str,
    dst_cols: ilist.IList[int, Nx],
    dst_rows: ilist.IList[int, Ny],
):
    assert_sorted(src_cols)
    assert_sorted(src_rows)
    assert_sorted(dst_cols)
    assert_sorted(dst_rows)

    assert len(src_cols) == len(
        dst_cols
    ), "src_cols and dst_cols must have the same length"
    assert len(src_rows) == len(
        dst_rows
    ), "src_rows and dst_rows must have the same length"

    assert src_block in ("GL", "GR"), "src_block must be either 'GL' or 'GR'"
    assert dst_block in ("GL", "GR"), "dst_block must be either 'GL' or 'GR'"

    x_tones = ilist.range(
        0, len(src_cols) * spec.get_int_constant(constant_id="code_size")
    )
    y_tones = ilist.range(0, len(src_rows))

    shift = schedule.device_fn(swap_block_impl, x_tones, y_tones)
    horizontal_move = schedule.device_fn(horizontal_move_impl, x_tones, y_tones)
    vertical_move = schedule.device_fn(vertical_move_impl, x_tones, y_tones)
    inv_horizontal_move = schedule.reverse(horizontal_move)
    inv_vertical_move = schedule.reverse(vertical_move)

    if src_block == dst_block:
        tmp_block = get_other_block(src_block)
        shift(src_block, src_cols, src_rows)
    else:
        tmp_block = src_block

    if src_cols != dst_cols:
        horizontal_move(tmp_block, src_rows, src_cols, dst_cols)

    if src_rows != dst_rows:
        vertical_move(tmp_block, dst_cols, src_rows, dst_rows)

    gate.top_hat_cz(spec.get_static_trap(zone_id="gate_zone"))

    if src_rows != dst_rows:
        inv_vertical_move(tmp_block, dst_cols, src_rows, dst_rows)

    if src_cols != dst_cols:
        inv_horizontal_move(tmp_block, src_rows, src_cols, dst_cols)

    if src_block == dst_block:
        shift(tmp_block, src_cols, src_rows)

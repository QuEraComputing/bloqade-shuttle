from typing import Any

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, spec, tweezer

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


@tweezer
def get_block(
    block_id: str,
    col_index: int,
    row_indices: ilist.IList[int, Any],
):
    """Returns the zone corresponding to the specified block and column.

    Args:
        block_id (str): The block identifier, either "GL" or "GR".
        col_index (int): The logical column index.
        row_indices (IList[int, Any]): The list of logical row indices.

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
    return block[col_index * code_size : (col_index + 1) * code_size, row_indices]


@tweezer
def move_by_shift(
    start_pos: grid.Grid[Any, Any],
    shifts: ilist.IList[tuple[float, float], Any],
    active_x: ilist.IList[int, Any] | slice,
    active_y: ilist.IList[int, Any] | slice,
):
    """Moves the specified atoms by applying a series of shifts.

    Args:
        start_pos (grid.Grid[Any, Any]): The starting position of the atoms.
        shifts (ilist.IList[tuple[float, float], Any]): The list of shifts to apply.
        active_x (ilist.IList[int, Any] | slice): The list or slice of active x indices.
        active_y (ilist.IList[int, Any] | slice): The list or slice of active y indices.
    """
    action.set_loc(start_pos)
    action.turn_on(active_x, active_y)

    current_pos = start_pos
    for shift in shifts:
        current_pos = grid.shift(current_pos, shift[0], shift[1])
        action.move(current_pos)

    action.turn_off(active_x, active_y)


@tweezer
def vertial_shift_impl(
    offset: int,
    src_col: int,
    src_rows: ilist.IList[int, Any],
):
    """Moves the specified rows within the given block.

    Args:
        block_id (str): The block identifier, either "GL" or "GR".
        offset (int): The offset to apply to the row indices, must be non-negative.
        src_col (int): The source column index.
        src_rows (ilist.IList[int, Any]): The list of source row indices.
    """
    assert offset >= 0, "offset must be non-negative"
    max_row = spec.get_int_constant(constant_id="logical_rows") - offset

    def check_row(row: int):
        assert row + offset < spec.get_int_constant(
            constant_id="logical_rows"
        ), "row index + offset must be less than `logical_rows`"

    ilist.for_each(check_row, src_rows)
    assert (
        len(src_rows) < max_row
    ), "Number of source rows must be less than `logical_rows - offset`"
    assert_sorted(src_rows)

    start_pos = get_block("GL", src_col, ilist.range(max_row))
    row_separation = spec.get_float_constant(constant_id="row_separation")
    col_separation = spec.get_float_constant(constant_id="col_separation")
    gate_spacing = spec.get_float_constant(constant_id="gate_spacing")

    if offset > 1:
        shifts = ilist.IList(
            [
                (0.0, row_separation * 0.5),
                (gate_spacing + col_separation * 0.5, 0.0),
                (0.0, row_separation * (offset - 0.5)),
                (-col_separation * 0.5, 0.0),
            ]
        )
    elif offset == 1:
        shifts = ilist.IList(
            [
                (0.0, row_separation * 0.5),
                (gate_spacing, 0.0),
                (0.0, row_separation * 0.5),
            ]
        )
    else:
        shifts = ilist.IList([(gate_spacing, 0.0)])

    move_by_shift(start_pos, shifts, action.ALL, src_rows)

    # validate the movement
    current_pos = start_pos
    for shift in shifts:
        current_pos = grid.shift(current_pos, shift[0], shift[1])

    expected_last_pos = get_block("GR", src_col, ilist.range(offset, max_row + offset))
    assert (
        current_pos == expected_last_pos
    ), "Final position does not match expected position"


@tweezer
def gr_zero_to_one(
    src_rows: ilist.IList[int, Any],
):
    """Moves the specified columns within the given block.

    Args:
        src_rows (ilist.IList[int, Any]): The rows to apply the transformation to.
    """
    logical_rows = spec.get_int_constant(constant_id="logical_rows")
    row_separation = spec.get_float_constant(constant_id="row_separation")
    col_separation = spec.get_float_constant(constant_id="col_separation")
    shift = col_separation * spec.get_float_constant(constant_id="code_size")

    shifts = ilist.IList(
        [
            (0.0, row_separation * 0.5),
            (shift, 0.0),
            (0.0, -row_separation * 0.5),
        ]
    )

    all_rows = ilist.range(logical_rows)
    start_pos = get_block("GR", 0, all_rows)

    move_by_shift(start_pos, shifts, action.ALL, src_rows)

    # validate the movement
    current_pos = start_pos
    for shift in shifts:
        current_pos = grid.shift(current_pos, shift[0], shift[1])

    expected_last_pos = get_block("GR", 1, all_rows)
    assert (
        current_pos == expected_last_pos
    ), "Final position does not match expected position"

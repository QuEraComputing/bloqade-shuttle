from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, spec, tweezer
from bloqade.shuttle.arch import ArchSpec, Layout

from .asserts import assert_sorted


def get_base_spec():

    ROW_SEPARATION = 10.0
    COL_SEPARATION = 8.0
    STORAGE_ALLY_WIDTH = 6.0
    GATE_SPACING = 2.0

    logical_rows = 5
    logical_cols = 2
    code_size = 7

    num_x = 17
    num_y = 5
    column_spacing = COL_SEPARATION
    row_spacing = ROW_SEPARATION
    gate_spacing = GATE_SPACING  # space between atoms for CZ gate.

    single_gate = grid.Grid.from_positions((0.0, gate_spacing), (0.0,))
    all_entangling_zone_traps = single_gate.repeat(
        num_x, num_y, column_spacing, row_spacing
    ).shift(-81.0, -20.0)

    reservoir_ally_width = STORAGE_ALLY_WIDTH
    reservoir_column_spacing = column_spacing + gate_spacing - reservoir_ally_width
    reservoir_row_spacing = 4.0
    num_reservoir_rows = 19

    reservoir_pair = grid.Grid.from_positions((0.0, reservoir_ally_width), (0.0,))

    reservoir = reservoir_pair.repeat(
        num_x, num_reservoir_rows, reservoir_column_spacing, reservoir_row_spacing
    )
    print(reservoir)

    top_reservoir = reservoir.shift(-81.0 - reservoir_ally_width, row_spacing * 3)
    bottom_reservoir = reservoir.shift(
        -81.0 - reservoir_ally_width,
        -3.0 * row_spacing - reservoir_row_spacing * (num_reservoir_rows - 1),
    )

    # various slices of the zones for convenience
    left_traps = all_entangling_zone_traps[::2, :]
    right_traps = all_entangling_zone_traps[1::2, :]
    aom_sites = left_traps.shift(-GATE_SPACING, 0)

    S_block_traps = top_reservoir[4 : 4 + 7 * 4, 8 : 8 + 5 * 2 : 2]
    M_block_traps = bottom_reservoir[4 : 4 + 7 * 4 :, 2 : 2 + 5 * 2 : 2]

    SL_block_traps = S_block_traps[: 2 * 7, :]
    SR_block_traps = S_block_traps[2 * 7 :, :]
    ML_block_traps = M_block_traps[: 2 * 7, :]
    MR_block_traps = M_block_traps[2 * 7 :, :]

    SL0_block_traps = SL_block_traps[::2, :]
    SL1_block_traps = SL_block_traps[1::2, :]
    SR0_block_traps = SR_block_traps[::2, :]
    SR1_block_traps = SR_block_traps[1::2, :]

    ML0_block_traps = ML_block_traps[::2, :]
    ML1_block_traps = ML_block_traps[1::2, :]
    MR0_block_traps = MR_block_traps[::2, :]
    MR1_block_traps = MR_block_traps[1::2, :]

    GL0_block_traps = left_traps[2 : 2 + 7 :, :]
    GR0_block_traps = right_traps[2 : 2 + 7 :, :]

    GL1_block_traps = left_traps[2 + 7 : 2 + 2 * 7 :, :]
    GR1_block_traps = right_traps[2 + 7 : 2 + 2 * 7 :, :]

    AOM0_block_positions = aom_sites[2 : 2 + 7, :]
    AOM1_block_positions = aom_sites[2 + 7 : 2 + 7 + 7, :]

    static_traps = {
        "traps": all_entangling_zone_traps,
        "left_traps": left_traps,
        "right_traps": right_traps,
        "top_reservoir": top_reservoir,
        "bottom_reservoir": bottom_reservoir,
        "SL0_block": SL0_block_traps,
        "SR0_block": SR0_block_traps,
        "SL1_block": SL1_block_traps,
        "SR1_block": SR1_block_traps,
        "ML0_block": ML0_block_traps,
        "MR0_block": MR0_block_traps,
        "ML1_block": ML1_block_traps,
        "MR1_block": MR1_block_traps,
        "GL0_block": GL0_block_traps,
        "GR0_block": GR0_block_traps,
        "GL1_block": GL1_block_traps,
        "GR1_block": GR1_block_traps,
    }

    layout = Layout(
        static_traps,
        {"GL0_block", "GL1_block"},
        {"traps"},
        {
            "left_traps",
            "right_traps",
            "traps",
            "GL0_block",
            "GR0_block",
            "GL1_block",
            "GR1_block",
        },
        special_grid={
            "aom_sites": aom_sites,
            "AOM0_block": AOM0_block_positions,
            "AOM1_block": AOM1_block_positions,
        },
    )
    return ArchSpec(
        layout,
        float_constants={
            "row_separation": ROW_SEPARATION,
            "col_separation": COL_SEPARATION,
            "gate_spacing": GATE_SPACING,
        },
        int_constants={
            "logical_rows": logical_rows,
            "logical_cols": logical_cols,
            "code_size": code_size,
        },
    )


N = TypeVar("N")


def get_subblock(
    block: grid.Grid, sublock_indices: ilist.IList[int, N]
) -> grid.Grid[Any, N]:
    all_columns = ilist.range(grid.shape(block)[0])
    return block.get_view(all_columns, sublock_indices)


@tweezer
def ltor_block_aom_move(
    left_subblocks: ilist.IList[int, N],
    right_subblocks: ilist.IList[int, N],
):

    assert_sorted(left_subblocks)
    assert_sorted(right_subblocks)

    assert len(left_subblocks) == len(
        right_subblocks
    ), "Left and right subblocks must have the same length."

    left_block = get_subblock(spec.get_static_trap(zone_id="GL0_block"), left_subblocks)
    right_block = get_subblock(
        spec.get_static_trap(zone_id="AOM1_block"), right_subblocks
    )

    row_separation = spec.get_float_constant(constant_id="row_separation")
    col_separation = spec.get_float_constant(constant_id="col_separation")
    gate_spacing = spec.get_float_constant(constant_id="gate_spacing")

    # AOM sites are already shifted by the gate spacing, so to shift to the center between the
    # two blocks, we need to shift the AOM sites by half the col separation minus the gate
    # spacing.
    shift_from_aom = col_separation / 2.0 - gate_spacing
    third_pos = grid.shift(right_block, -shift_from_aom, 0.0)
    first_pos = grid.shift(left_block, 0.0, row_separation / 2.0)
    second_pos = grid.from_positions(grid.get_xpos(third_pos), grid.get_ypos(first_pos))

    action.set_loc(left_block)
    action.turn_on(action.ALL, action.ALL)
    action.move(first_pos)
    action.move(second_pos)
    action.move(third_pos)
    action.move(right_block)

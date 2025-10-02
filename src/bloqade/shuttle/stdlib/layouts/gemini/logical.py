from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, schedule, spec, tweezer
from bloqade.shuttle.prelude import move

from ..asserts import assert_sorted
from .base_spec import get_base_spec


def get_logical_spec():
    arch_spec = get_base_spec()

    gate_zone = arch_spec.layout.static_traps["gate_zone"]
    aom_sites = arch_spec.layout.special_grid["aom_sites"]
    top_reservoir = arch_spec.layout.static_traps["top_reservoir"]
    bottom_reservoir = arch_spec.layout.static_traps["bottom_reservoir"]

    left_traps = gate_zone[::2, :]
    right_traps = gate_zone[1::2, :]
    S_block_traps = top_reservoir[4 : 4 + 7 * 4, 8 : 8 + 5 * 2 : 2]
    M_block_traps = bottom_reservoir[4 : 4 + 7 * 4 :, 2 : 2 + 5 * 2 : 2]

    SL_block_traps = S_block_traps[: 2 * 7, :]
    SR_block_traps = S_block_traps[2 * 7 :, :]
    ML_block_traps = M_block_traps[: 2 * 7, :]
    MR_block_traps = M_block_traps[2 * 7 :, :]

    SL0_block = SL_block_traps[::2, :]
    SL1_block = SL_block_traps[1::2, :]
    SR0_block = SR_block_traps[::2, :]
    SR1_block = SR_block_traps[1::2, :]

    ML0_block = ML_block_traps[::2, :]
    ML1_block = ML_block_traps[1::2, :]
    MR0_block = MR_block_traps[::2, :]
    MR1_block = MR_block_traps[1::2, :]

    GL0_block = left_traps[2 : 2 + 7 :, :]
    GR0_block = right_traps[2 : 2 + 7 :, :]

    GL1_block = left_traps[2 + 7 : 2 + 2 * 7 :, :]
    GR1_block = right_traps[2 + 7 : 2 + 2 * 7 :, :]

    AOM0_block = aom_sites[2 : 2 + 7, :]
    AOM1_block = aom_sites[2 + 7 : 2 + 7 + 7, :]

    additional_static_traps = {
        "left_gate_zone_sites": left_traps,
        "right_gate_zone_sites": right_traps,
        "top_reservoir_sites": top_reservoir,
        "bottom_reservoir_sites": bottom_reservoir,
        "GL0_block": GL0_block,
        "GL1_block": GL1_block,
        "GR0_block": GR0_block,
        "GR1_block": GR1_block,
        "AOM0_block": AOM0_block,
        "AOM1_block": AOM1_block,
        "SL0_block": SL0_block,
        "SL1_block": SL1_block,
        "SR0_block": SR0_block,
        "SR1_block": SR1_block,
        "ML0_block": ML0_block,
        "ML1_block": ML1_block,
        "MR0_block": MR0_block,
        "MR1_block": MR1_block,
    }

    arch_spec.layout.static_traps.update(additional_static_traps)
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


@move
def entangle(
    left_subblocks: ilist.IList[int, N],
    right_subblocks: ilist.IList[int, N],
):
    x_tones = ilist.range(spec.get_int_constant(constant_id="code_size"))
    y_tones = ilist.range(len(left_subblocks))

    device_func = schedule.device_fn(ltor_block_aom_move, x_tones, y_tones)
    rev_func = schedule.reverse(device_func)

    device_func(left_subblocks, right_subblocks)
    gate.top_hat_cz(spec.get_static_trap(zone_id="gate_zone"))
    rev_func(left_subblocks, right_subblocks)

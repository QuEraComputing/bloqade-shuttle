import itertools
import typing
from itertools import repeat

import pytest
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import arch, move
from bloqade.shuttle.arch import ArchSpecInterpreter
from bloqade.shuttle.codegen import TraceInterpreter, taskgen
from bloqade.shuttle.stdlib.layouts.gemini import logical


def get_logical_spec_tyler() -> arch.ArchSpec:
    ROW_SEPARATION = 10.0
    COL_SEPARATION = 8.0
    STORAGE_ALLY_WIDTH = 6.0
    GATE_SPACING = 2.0

    num_x = 17
    num_y = 5
    column_spacing = COL_SEPARATION
    row_spacing = ROW_SEPARATION
    gate_spacing = GATE_SPACING  # space between atoms for CZ gate.

    x_spacing = sum(repeat((gate_spacing, column_spacing), num_x - 1), ()) + (
        gate_spacing,
    )
    y_spacing = tuple(repeat(row_spacing, num_y - 1))
    all_entangling_zone_traps = grid.Grid(
        x_spacing, y_spacing, -81.0, -20.0
    )  # offset to center the grid such that 0,0 is the middle of the AOD.
    left_trap_x_indices = ilist.IList(range(0, num_x * 2, 2))
    right_trap_x_indices = ilist.IList(range(1, num_x * 2, 2))
    all_y_indices = ilist.IList(range(num_y))
    left_traps = all_entangling_zone_traps.get_view(left_trap_x_indices, all_y_indices)
    right_traps = all_entangling_zone_traps.get_view(
        right_trap_x_indices, all_y_indices
    )

    aom_sites = left_traps.shift(-2, 0)

    reservoir_ally_width = STORAGE_ALLY_WIDTH
    reservoir_column_spacing = column_spacing + gate_spacing - reservoir_ally_width
    reservoir_row_spacing = 4.0
    num_reservoir_rows = 19

    reservoir_x_spacing = sum(
        repeat((reservoir_ally_width, reservoir_column_spacing), num_x - 1), ()
    ) + (reservoir_ally_width,)
    reservoir_y_spacing = tuple(repeat(reservoir_row_spacing, num_reservoir_rows - 1))

    top_reservoir = grid.Grid(
        reservoir_x_spacing,
        reservoir_y_spacing,
        -81.0 - reservoir_ally_width,
        row_spacing * 3,
    )
    bottom_reservoir = grid.Grid(
        reservoir_x_spacing,
        reservoir_y_spacing,
        -81.0 - reservoir_ally_width,
        -3.0 * row_spacing - reservoir_row_spacing * (num_reservoir_rows - 1),
    )

    SL0_block_x_indices = ilist.IList(range(4, 4 + 7 * 2, 2))
    SL0_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SL0_block_traps = top_reservoir.get_view(SL0_block_x_indices, SL0_block_y_indices)

    SR0_block_x_indices = ilist.IList(range(5, 5 + 7 * 2, 2))
    SR0_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SR0_block_traps = top_reservoir.get_view(SR0_block_x_indices, SR0_block_y_indices)

    SL1_block_x_indices = ilist.IList(range(4 + 7 * 2, 4 + 7 * 2 + 7 * 2, 2))
    SL1_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SL1_block_traps = top_reservoir.get_view(SL1_block_x_indices, SL1_block_y_indices)

    SR1_block_x_indices = ilist.IList(range(5 + 7 * 2, 5 + 7 * 2 + 7 * 2, 2))
    SR1_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SR1_block_traps = top_reservoir.get_view(SR1_block_x_indices, SR1_block_y_indices)

    ML0_block_x_indices = ilist.IList(range(4, 4 + 7 * 2, 2))
    ML0_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    ML0_block_traps = bottom_reservoir.get_view(
        ML0_block_x_indices, ML0_block_y_indices
    )

    MR0_block_x_indices = ilist.IList(range(5, 5 + 7 * 2, 2))
    MR0_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    MR0_block_traps = bottom_reservoir.get_view(
        MR0_block_x_indices, MR0_block_y_indices
    )

    ML1_block_x_indices = ilist.IList(range(4 + 7 * 2, 4 + 7 * 2 + 7 * 2, 2))
    ML1_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    ML1_block_traps = bottom_reservoir.get_view(
        ML1_block_x_indices, ML1_block_y_indices
    )

    MR1_block_x_indices = ilist.IList(range(5 + 7 * 2, 5 + 7 * 2 + 7 * 2, 2))
    MR1_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    MR1_block_traps = bottom_reservoir.get_view(
        MR1_block_x_indices, MR1_block_y_indices
    )

    G0_block_x_indices = ilist.IList(range(2, 2 + 7))
    GL0_block_traps = left_traps.get_view(G0_block_x_indices, all_y_indices)
    GR0_block_traps = right_traps.get_view(G0_block_x_indices, all_y_indices)

    G1_block_x_indices = ilist.IList(range(2 + 7, 2 + 7 + 7))
    GL1_block_traps = left_traps.get_view(G1_block_x_indices, all_y_indices)
    GR1_block_traps = right_traps.get_view(G1_block_x_indices, all_y_indices)

    static_traps = {
        "gate_zone": all_entangling_zone_traps,
        "left_gate_zone_sites": left_traps,
        "right_gate_zone_sites": right_traps,
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

    gemini_layout = arch.Layout(
        static_traps=static_traps,
        fillable=set(
            [
                "GL0_block",
                "GL1_block",
            ]
        ),
        has_cz=set(["gate_zone"]),
        has_local=set(["GL0_block", "GL1_block", "GR0_block", "GR1_block"]),
        special_grid={"aom_sites": aom_sites},
    )

    logical_rows = 5
    logical_cols = 2
    code_size = 7

    spec_value = arch.ArchSpec(
        layout=gemini_layout,
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

    return spec_value


def test_against_tyler():
    old_spec = get_logical_spec_tyler()
    new_spec = logical.get_spec()

    for key in old_spec.layout.static_traps:
        new_grid = new_spec.layout.static_traps.get(key)
        old_grid = old_spec.layout.static_traps[key]
        assert new_grid is not None, f"Missing grid for key {key}"
        assert new_grid.x_spacing == old_grid.x_spacing, f"Grid mismatch for key {key}"
        assert new_grid.y_spacing == old_grid.y_spacing, f"Grid mismatch for key {key}"
        assert new_grid.x_init == old_grid.x_init, f"Grid mismatch for key {key}"
        assert new_grid.y_init == old_grid.y_init, f"Grid mismatch for key {key}"

    for key in old_spec.layout.special_grid:
        new_grid = new_spec.layout.special_grid.get(key)
        old_grid = old_spec.layout.special_grid[key]
        assert new_grid is not None, f"Missing grid for key {key}"
        assert new_grid.x_spacing == old_grid.x_spacing, f"Grid mismatch for key {key}"
        assert new_grid.y_spacing == old_grid.y_spacing, f"Grid mismatch for key {key}"
        assert new_grid.x_init == old_grid.x_init, f"Grid mismatch for key {key}"
        assert new_grid.y_init == old_grid.y_init, f"Grid mismatch for key {key}"


N = typing.TypeVar("N")


def run_trace(
    left_subblocks: ilist.IList[int, N],
    right_subblocks: ilist.IList[int, N],
):

    device_fn = ArchSpecInterpreter(
        dialects=move, arch_spec=(arch_spec := logical.get_spec())
    ).run(logical.get_device_fn, (left_subblocks, right_subblocks))
    trace_results = TraceInterpreter(arch_spec=arch_spec).run_trace(
        device_fn.move_fn, (left_subblocks, right_subblocks), kwargs={}
    )

    return trace_results, arch_spec


def is_sorted(lst: ilist.IList[int, N]) -> bool:
    return all(x <= y for x, y in zip(lst, lst[1:]))


test_indices = [
    ilist.IList([0]),
    ilist.IList([1]),
    ilist.IList([1, 3]),
    ilist.IList([0, 2, 4]),
    ilist.IList([0, 1, 2, 3, 4]),
    ilist.IList([3, 2, 1]),
]


@pytest.mark.parametrize(
    "left_subblocks,right_subblocks", itertools.product(test_indices, repeat=2)
)
def test_aom_move(
    left_subblocks: ilist.IList[int, N], right_subblocks: ilist.IList[int, N]
):

    if not (is_sorted(left_subblocks) and is_sorted(right_subblocks)) or len(
        left_subblocks
    ) != len(right_subblocks):
        with pytest.raises(AssertionError):
            run_trace(left_subblocks, right_subblocks)

        return
    else:
        actions, arch_spec = run_trace(left_subblocks, right_subblocks)

    GL0_block = arch_spec.layout.static_traps["GL0_block"]
    AOM1_block = arch_spec.layout.special_grid["AOM1_block"]

    set_waypoint, turn_on, movement = actions

    start_pos = GL0_block[:, left_subblocks]
    end_pos = AOM1_block[:, right_subblocks]

    x_shift = (
        arch_spec.float_constants["col_separation"] / 2.0
        - arch_spec.float_constants["gate_spacing"]
    )
    y_shift = arch_spec.float_constants["row_separation"] / 2.0

    first_pos = start_pos.shift(0, y_shift)
    third_pos = end_pos.shift(-x_shift, 0.0)
    mid_pos = grid.Grid.from_positions(third_pos.x_positions, first_pos.y_positions)

    expected_movement = taskgen.WayPointsAction(
        [start_pos, first_pos, mid_pos, third_pos, end_pos]
    )

    assert set_waypoint == taskgen.WayPointsAction([start_pos])
    assert (
        isinstance(turn_on, taskgen.TurnOnXYSliceAction)
        and turn_on.x_tone_indices == slice(None)
        and turn_on.y_tone_indices == slice(None)
    )
    assert movement == expected_movement


# if __name__ == "__main__":
#     test_aom_move()

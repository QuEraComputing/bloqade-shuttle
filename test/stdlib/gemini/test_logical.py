import itertools
import typing
from itertools import repeat

import pytest
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import arch
from bloqade.shuttle.codegen import TraceInterpreter, taskgen
from bloqade.shuttle.stdlib.layouts.gemini import logical


def is_sorted(lst):
    return all(ele1 < ele2 for ele1, ele2 in zip(lst, lst[1:]))


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

swap_block_test_cases = [
    (ilist.IList([0]), ilist.IList([0, 2, 4])),
    (ilist.IList([1]), ilist.IList([1, 3])),
    (ilist.IList([0, 1]), ilist.IList([0, 1, 2, 3, 4])),
    (ilist.IList([0, 1]), ilist.IList([0, 2, 4])),
    (ilist.IList([1, 0]), ilist.IList([0, 2, 4])),
]


@pytest.mark.parametrize("x_indices, y_indices", swap_block_test_cases)
def test_swap_block_impl(
    x_indices: ilist.IList[int, typing.Any], y_indices: ilist.IList[int, typing.Any]
):
    spec = logical.get_spec()
    ti = TraceInterpreter(spec)

    args = ("GL", x_indices, y_indices)

    has_error = not is_sorted(x_indices) or not is_sorted(y_indices)

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(logical.swap_block_impl, args=args, kwargs={})
        return

    actions = ti.run_trace(logical.swap_block_impl, args=args, kwargs={})
    code_size = spec.int_constants["code_size"]

    physical_indices = (range(i * code_size, (i + 1) * code_size) for i in x_indices)
    x_physical_indices = ilist.IList(sum(map(tuple, physical_indices), ()))

    start_grid = spec.layout.static_traps["GL_blocks"][x_physical_indices, y_indices]
    end_grid = spec.layout.static_traps["GR_blocks"][x_physical_indices, y_indices]

    has_error = not is_sorted(x_indices) or not is_sorted(y_indices)

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(logical.swap_block_impl, args=args, kwargs={})
        return

    expected_actions = [
        taskgen.WayPointsAction([start_grid]),
        taskgen.TurnOnXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([start_grid, end_grid]),
        taskgen.TurnOffXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([end_grid]),
    ]

    for a, e in itertools.zip_longest(actions, expected_actions):
        assert a == e, f"Action {a} does not match expected {e}"


vertical_move_test_cases = [
    ("GL", ilist.IList([0]), ilist.IList([0, 2]), ilist.IList([1, 4])),
    ("GR", ilist.IList([1]), ilist.IList([1, 3]), ilist.IList([0, 2])),
    ("GL", ilist.IList([0, 1]), ilist.IList([0, 1, 2]), ilist.IList([2, 3, 4])),
    ("GR", ilist.IList([1, 0]), ilist.IList([0, 2]), ilist.IList([1, 4])),
    ("GR", ilist.IList([1, 0]), ilist.IList([0, 2]), ilist.IList([1])),
]


@pytest.mark.parametrize(
    "block_id, col_indices, src_rows, dst_rows", vertical_move_test_cases
)
def test_vertical_move_impl(
    block_id: str,
    col_indices: ilist.IList[int, typing.Any],
    src_rows: ilist.IList[int, N],
    dst_rows: ilist.IList[int, N],
):
    spec = logical.get_spec()
    ti = TraceInterpreter(spec)

    args = (block_id, col_indices, src_rows, dst_rows)

    has_error = (
        len(src_rows) != len(dst_rows)
        or not is_sorted(src_rows)
        or not is_sorted(dst_rows)
        or not is_sorted(col_indices)
    )

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(logical.vertical_move_impl, args=args, kwargs={})

        return

    trace_results = ti.run_trace(logical.vertical_move_impl, args=args, kwargs={})
    code_size = spec.int_constants["code_size"]

    physical_indices = (range(i * code_size, (i + 1) * code_size) for i in col_indices)
    x_physical_indices = ilist.IList(sum(map(tuple, physical_indices), ()))

    start_grid = spec.layout.static_traps[f"{block_id}_blocks"][
        x_physical_indices, src_rows
    ]
    end_grid = spec.layout.static_traps[f"{block_id}_blocks"][
        x_physical_indices, dst_rows
    ]

    col_separation = spec.float_constants["col_separation"]
    x_shift = col_separation / 2 if block_id == "GR" else -(col_separation / 2)

    mid_1 = start_grid.shift(x_shift, 0.0)
    mid_2 = end_grid.shift(x_shift, 0.0)

    expected_actions = [
        taskgen.WayPointsAction([start_grid]),
        taskgen.TurnOnXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([start_grid, mid_1, mid_2, end_grid]),
        taskgen.TurnOffXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([end_grid]),
    ]

    for a, e in itertools.zip_longest(trace_results, expected_actions):
        assert a == e, f"Action {a} does not match expected {e}"


horizontal_move_test_cases = [
    ("GL", ilist.IList([0, 2, 3]), ilist.IList([0]), ilist.IList([1])),
    ("GR", ilist.IList([1, 3, 4]), ilist.IList([1]), ilist.IList([0])),
    ("GL", ilist.IList([0, 1, 2, 3, 4]), ilist.IList([0]), ilist.IList([1])),
    ("GR", ilist.IList([1, 0]), ilist.IList([0]), ilist.IList([1])),
    ("GR", ilist.IList([0, 1]), ilist.IList([0]), ilist.IList([0, 1])),
]


@pytest.mark.parametrize(
    "block_id, row_indices, src_cols, dst_cols", horizontal_move_test_cases
)
def test_horizontal_move_impl(
    block_id: str,
    row_indices: ilist.IList[int, typing.Any],
    src_cols: ilist.IList[int, N],
    dst_cols: ilist.IList[int, N],
):
    spec = logical.get_spec()
    ti = TraceInterpreter(spec)

    args = (block_id, row_indices, src_cols, dst_cols)

    has_error = (
        len(src_cols) != len(dst_cols)
        or not is_sorted(row_indices)
        or not is_sorted(dst_cols)
        or not is_sorted(src_cols)
    )

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(logical.horizontal_move_impl, args=args, kwargs={})

        return

    trace_results = ti.run_trace(logical.horizontal_move_impl, args=args, kwargs={})
    code_size = spec.int_constants["code_size"]

    src_physical_indices = (range(i * code_size, (i + 1) * code_size) for i in src_cols)
    dst_physical_indices = (range(i * code_size, (i + 1) * code_size) for i in dst_cols)
    src_x_physical_indices = ilist.IList(sum(map(tuple, src_physical_indices), ()))
    dst_x_physical_indices = ilist.IList(sum(map(tuple, dst_physical_indices), ()))

    start_grid = spec.layout.static_traps[f"{block_id}_blocks"][
        src_x_physical_indices, row_indices
    ]
    end_grid = spec.layout.static_traps[f"{block_id}_blocks"][
        dst_x_physical_indices, row_indices
    ]

    row_separation = spec.float_constants["row_separation"]
    y_shift = row_separation / 2

    mid_1 = start_grid.shift(0.0, y_shift)
    mid_2 = end_grid.shift(0.0, y_shift)

    expected_actions = [
        taskgen.WayPointsAction([start_grid]),
        taskgen.TurnOnXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([start_grid, mid_1, mid_2, end_grid]),
        taskgen.TurnOffXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([end_grid]),
    ]

    for a, e in itertools.zip_longest(trace_results, expected_actions):
        assert a == e, f"Action {a} does not match expected {e}"

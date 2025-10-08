import itertools
import typing
from typing import Any

import pytest
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle.codegen import TraceInterpreter, taskgen
from bloqade.shuttle.stdlib.layouts.two_col_zone import (
    get_spec,
    rearrange_impl_horizontal_vertical,
    rearrange_impl_horizontal_vertical_multi_row,
)

move_test_cases = [
    (
        ilist.IList([0, 2, 4, 6]),
        ilist.IList([0]),
        ilist.IList([1, 3, 5, 7]),
        ilist.IList([1]),
        [
            grid.Grid((12.0, 12.0, 12.0), (), -3.0, 0.0),
            grid.Grid((12.0, 12.0, 12.0), (), -3.0, 7.0),
            grid.Grid((12.0, 12.0, 12.0), (), 2.0, 7.0),
        ],
    ),
    (
        ilist.IList([0, 1, 2, 3]),
        ilist.IList([0]),
        ilist.IList([4, 5, 6, 7]),
        ilist.IList([1]),
        [
            grid.Grid((8.0, 4.0, 8.0), (), -3.0, 0.0),
            grid.Grid((8.0, 4.0, 8.0), (), -3.0, 7.0),
            grid.Grid((2.0, 10.0, 2.0), (), 24.0, 7.0),
        ],
    ),
    (
        ilist.IList([0, 1, 6, 7]),
        ilist.IList([1]),
        ilist.IList([1, 2, 7, 8]),
        ilist.IList([0]),
        [
            grid.Grid((8.0, 28.0, 8.0), (), -3.0, 10.0),
            grid.Grid((8.0, 28.0, 8.0), (), -3.0, 3.0),
            grid.Grid((10.0, 26.0, 10.0), (), 2.0, 3.0),
        ],
    ),
    (  # error case
        ilist.IList([0, 2, 4, 6]),
        ilist.IList([0]),
        ilist.IList([1, 3]),
        ilist.IList([1]),
        [],
    ),
]

N = typing.TypeVar("N")


@pytest.mark.parametrize(
    "src_cols, src_rows, dst_cols, dst_rows, way_points", move_test_cases
)
def test_horizontal_move_impl(
    src_cols: ilist.IList[int, N],
    src_rows: ilist.IList[int, N],
    dst_cols: ilist.IList[int, N],
    dst_rows: ilist.IList[int, N],
    way_points: list[grid.Grid[Any, Any]],
):
    spec_value = get_spec(10, 2, spacing=10.0, gate_spacing=2.0)
    zone = spec_value.layout.static_traps["traps"]

    args = (src_cols, src_rows, dst_cols, dst_rows)

    has_error = len(src_cols) != len(dst_cols)
    ti = TraceInterpreter(spec_value)

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(rearrange_impl_horizontal_vertical, args=args, kwargs={})

        return

    trace_results = ti.run_trace(
        rearrange_impl_horizontal_vertical, args=args, kwargs={}
    )

    start_pos = zone.get_view(src_cols, src_rows)
    end_pos = zone.get_view(dst_cols, dst_rows)

    expected_movement = [start_pos] + way_points + [end_pos]

    expected_actions = [
        taskgen.WayPointsAction([start_pos]),
        taskgen.TurnOnXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction(expected_movement),
        taskgen.TurnOffXYSliceAction(slice(None), slice(None)),
        taskgen.WayPointsAction([end_pos]),
    ]

    for a, e in itertools.zip_longest(trace_results, expected_actions):
        assert a == e, f"Action {a} does not match expected {e}"


move_test_cases = [
    (
        ilist.IList([(0, 0), (0, 1), (1, 1), (2, 1)]),
        ilist.IList([0, 1, 2]),
        ilist.IList([0, 1]),
        ilist.IList([(2, 2), (2, 3), (4, 3), (5, 3)]),
        ilist.IList([2, 4, 5]),
        ilist.IList([2, 3]),
        [
            # taskgen.WayPointsAction(
            #     [
            #         grid.Grid((2.0, 10.0), (10.0,), 0.0, 0.0),
            #     ]
            # ),
            taskgen.TurnOnXYSliceAction(slice(0, 1), slice(0, 1)),
            taskgen.WayPointsAction(
                [
                    grid.Grid((2.0, 10.0), (10.0,), 0.0, 0.0),
                    grid.Grid((5.0, 10.0), (7.0,), -3.0, 3.0),
                    grid.Grid((2.0, 10.0), (7.0,), 0.0, 3.0),
                ]
            ),
            taskgen.TurnOnXYSliceAction(slice(1, 3), slice(0, 1)),
            taskgen.WayPointsAction(
                [
                    grid.Grid((2.0, 10.0), (7.0,), 0.0, 3.0),
                    grid.Grid((8.0, 4.0), (10.0,), -3.0, 3.0),
                    grid.Grid((8.0, 4.0), (10.0,), -3.0, 17.0),
                    grid.Grid((12.0, 2.0), (10.0,), 12.0, 17.0),
                    grid.Grid((12.0, 2.0), (10.0,), 12.0, 20.0),
                ]
            ),
            taskgen.TurnOffXYSliceAction(slice(None), slice(None)),
            # taskgen.WayPointsAction(
            #     [
            #         grid.Grid((12.0, 2.0), (10.0,), 12.0, 20.0),
            #     ]
            # ),
        ],
    ),
    (  # error case
        ilist.IList([(0, 0), (0, 1), (1, 1), (2, 1)]),
        ilist.IList([0, 1, 2]),
        ilist.IList([0, 1]),
        ilist.IList([(2, 2)]),
        ilist.IList([2]),
        ilist.IList([2]),
        [],
    ),
]

N = typing.TypeVar("N")


@pytest.mark.parametrize(
    "src, src_cols, src_rows, dst, dst_cols, dst_rows, expected_actions",
    move_test_cases,
)
def test_horizontal_move_multi_row_impl(
    src: ilist.IList[tuple[int, int], N],
    src_cols: ilist.IList[int, N],
    src_rows: ilist.IList[int, N],
    dst: ilist.IList[tuple[int, int], N],
    dst_cols: ilist.IList[int, N],
    dst_rows: ilist.IList[int, N],
    expected_actions: list[Any],
):
    spec_value = get_spec(10, 4, spacing=10.0, gate_spacing=2.0)
    zone = spec_value.layout.static_traps["traps"]

    args = (src, src_cols, src_rows, dst, dst_cols, dst_rows)

    has_error = len(src) != len(dst)
    ti = TraceInterpreter(spec_value)

    if has_error:
        with pytest.raises(AssertionError):
            ti.run_trace(
                rearrange_impl_horizontal_vertical_multi_row, args=args, kwargs={}
            )

        return

    trace_results = ti.run_trace(
        rearrange_impl_horizontal_vertical_multi_row, args=args, kwargs={}
    )

    start_pos = zone.get_view(src_cols, src_rows)
    end_pos = zone.get_view(dst_cols, dst_rows)

    expected_actions = (
        [taskgen.WayPointsAction([start_pos])]
        + expected_actions
        + [taskgen.WayPointsAction([end_pos])]
    )

    for a, e in itertools.zip_longest(trace_results, expected_actions):
        assert a == e, f"Action {a} does not match expected {e}"

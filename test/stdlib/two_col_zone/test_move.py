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

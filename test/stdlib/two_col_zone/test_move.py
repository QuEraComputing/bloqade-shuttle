from kirin.dialects import ilist

from bloqade.shuttle import move
from bloqade.shuttle.arch import ArchSpecInterpreter
from bloqade.shuttle.codegen import TraceInterpreter, taskgen
from bloqade.shuttle.stdlib.layouts.two_col_zone import (
    get_device_fn,
    get_spec,
    rearrange_impl_horizontal_vertical,
)


def test_aom_move():
    spec_value = get_spec(10, 2)
    zone = spec_value.layout.static_traps["traps"]
    qubit_init_x = ilist.IList([0, 2, 4, 6])
    qubit_init_y = ilist.IList([0])

    qubit_final_x = ilist.IList([1, 3, 5, 7])
    qubit_final_y = ilist.IList([1])

    device_fn = ArchSpecInterpreter(
        dialects=move, arch_spec=(arch_spec := spec_value)
    ).run(
        get_device_fn,
        (
            qubit_init_x,
            qubit_init_y,
            qubit_final_x,
            qubit_final_y,
            rearrange_impl_horizontal_vertical,
        ),
    )
    actions = TraceInterpreter(arch_spec=arch_spec).run_trace(
        device_fn.move_fn,
        (qubit_init_x, qubit_init_y, qubit_final_x, qubit_final_y),
        kwargs={},
    )
    set_waypoint_init, turn_on, movement, turn_off, set_waypoint_end = actions

    start_pos = zone.get_view(qubit_init_x, qubit_init_y)
    end_pos = zone.get_view(qubit_final_x, qubit_final_y)

    first_pos = start_pos.shift(-3.0, 0.0)
    second_pos = first_pos.shift(0.0, 7.0)
    third_pos = first_pos.shift(5.0, 7.0)

    expected_movement = taskgen.WayPointsAction(
        [start_pos, first_pos, second_pos, third_pos, end_pos]
    )

    assert set_waypoint_init == taskgen.WayPointsAction([start_pos])
    assert set_waypoint_end == taskgen.WayPointsAction([end_pos])
    assert (
        isinstance(turn_on, taskgen.TurnOnXYSliceAction)
        and turn_on.x_tone_indices == slice(None)
        and turn_on.y_tone_indices == slice(None)
    )
    assert (
        isinstance(turn_off, taskgen.TurnOffXYSliceAction)
        and turn_off.x_tone_indices == slice(None)
        and turn_off.y_tone_indices == slice(None)
    )
    assert movement == expected_movement

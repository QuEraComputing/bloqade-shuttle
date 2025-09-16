from itertools import repeat
from typing import Any, Literal, TypeVar, List


from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, init, measure, schedule, spec

from bloqade.shuttle.prelude import move, tweezer

from bloqade.shuttle.stdlib.layouts.asserts import assert_sorted

from bloqade.shuttle.visualizer import MatplotlibRenderer, PathVisualizer

# Define type variables for generic programming
NumX = TypeVar('NumX', bound=int)
NumY = TypeVar('NumY', bound=int)

@tweezer
def entangle_move_ltor(
    controls: grid.Grid[Any, Literal[1]],
    targets: grid.Grid[Any, Literal[1]],
):

    start_x = grid.get_xpos(controls)
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, 2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    action.set_loc(pos_1)
    action.turn_on(action.ALL, [0])
    action.move(pos_2)

@tweezer
def entangle_move_rtor(
    controls: grid.Grid[Any, Literal[1]],
    targets: grid.Grid[Any, Literal[1]],
):

    start_x = grid.get_xpos(grid.shift(controls, 2, 0))
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, 2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    action.set_loc(pos_1)
    action.turn_on(action.ALL, [0])
    action.move(pos_2)

@move
def run_entangle_move_ltor(
    controls: grid.Grid[Any, Literal[1]],
    targets: grid.Grid[Any, Literal[1]],
):
    xtones = ilist.range(len(controls.x_positions))
    ytones = ilist.range(len(controls.y_positions))

    dtask = schedule.device_fn(entangle_move_ltor, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

@move
def run_entangle_move_rtor(
    controls: grid.Grid[Any, Literal[1]],
    targets: grid.Grid[Any, Literal[1]],
):
    xtones = ilist.range(len(controls.x_positions))
    ytones = ilist.range(len(controls.y_positions))

    dtask = schedule.device_fn(entangle_move_rtor, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

def generate_moves():

    num_x = 14
    num_y = 5
    spacing = 10.0
    gate_spacing = 2.0

    x_spacing = sum(repeat((gate_spacing, spacing), num_x - 1), ()) + (gate_spacing,)
    y_spacing = tuple(repeat(spacing, num_y - 1))
    all_traps = grid.Grid(x_spacing, y_spacing, 0.0, 0.0)
    left_trap_x_indices = ilist.IList(range(0, num_x * 2, 2))
    right_trap_x_indices = ilist.IList(range(1, num_x * 2, 2))
    all_y_indices = ilist.IList(range(num_y))
    left_traps = all_traps.get_view(left_trap_x_indices, all_y_indices)
    right_traps = all_traps.get_view(right_trap_x_indices, all_y_indices)

    static_traps = {
        "traps": all_traps,
        "left_traps": left_traps,
        "right_traps": right_traps,
    }

    home_x_indices = {
        logical_q_idx: ilist.IList([(q_idx % 14) for q_idx in range(logical_q_idx * 7, logical_q_idx * 7 + 7)]) for
        logical_q_idx in range(int(num_x * num_y / 7))
    }

    home_y_indices = {
        logical_q_idx: ilist.IList([q_idx // 14 for q_idx in range(logical_q_idx * 7, logical_q_idx * 7 + 7)]) for
        logical_q_idx in range(int(num_x * num_y / 7))
    }

    def add_zones(control_logicals, target_logicals, move_index):
        control_x_indices = []
        control_y_indices = []
        for c in control_logicals:
            control_x_indices.extend(home_x_indices[c])
            control_y_indices.extend(home_y_indices[c])

        target_x_indices = []
        target_y_indices = []
        for t in target_logicals:
            target_x_indices.extend(home_x_indices[t])
            target_y_indices.extend(home_y_indices[t])

        control_x_indices = ilist.IList(sorted(set(control_x_indices)))
        control_y_indices = ilist.IList(sorted(set(control_y_indices)))
        target_x_indices = ilist.IList(sorted(set(target_x_indices)))
        target_y_indices = ilist.IList(sorted(set(target_y_indices)))

        qubit_moves = {
            f'controls_{move_index}': left_traps.get_view(control_x_indices, control_y_indices),
            f'targets_{move_index}': left_traps.get_view(target_x_indices, target_y_indices),
        } #controls will move to targets

        static_traps.update(qubit_moves)

    add_zones(control_logicals = [0,2,4,6], target_logicals = [2,4,6,8], move_index=0)
    add_zones(control_logicals=[0, 2, 4], target_logicals=[4, 6, 8], move_index=1)
    add_zones(control_logicals=[0, 2], target_logicals=[6, 8], move_index=2)
    add_zones(control_logicals=[0], target_logicals=[8], move_index=3)
    add_zones(control_logicals=[8], target_logicals=[0], move_index=4)
    add_zones(control_logicals=[8, 6], target_logicals=[2, 0], move_index=5)
    add_zones(control_logicals=[8, 6, 4], target_logicals=[4, 2, 0], move_index=6)
    add_zones(control_logicals=[8, 6, 4, 2], target_logicals=[6, 4, 2, 0], move_index=7)

    add_zones(control_logicals = [1,3,5,7], target_logicals = [3,5,7,9], move_index=8)
    add_zones(control_logicals=[1, 3, 5], target_logicals=[5, 7, 9], move_index=9)
    add_zones(control_logicals=[1, 3], target_logicals=[7, 9], move_index=10)
    add_zones(control_logicals=[1], target_logicals=[9], move_index=11)
    add_zones(control_logicals=[9], target_logicals=[1], move_index=12)
    add_zones(control_logicals=[9, 7], target_logicals=[3, 1], move_index=13)
    add_zones(control_logicals=[9, 7, 5], target_logicals=[5, 3, 1], move_index=14)
    add_zones(control_logicals=[9, 7, 5, 3], target_logicals=[7, 5, 3, 1], move_index=15)

    add_zones(control_logicals=[0,2,4,6,8], target_logicals=[1,3,5,7,9], move_index=16)

    add_zones(control_logicals=[0,2,4,6,8], target_logicals=[0,2,4,6,8], move_index=17)
    add_zones(control_logicals=[1,3,5,7,9], target_logicals=[1,3,5,7,9], move_index=18)

    layout = spec.Layout(
        static_traps=static_traps,
        fillable=set(["left_traps"]),
        has_cz=set(["traps"]),
        has_local=set(["left_traps"]),
    )

    layout.show()

    spec_value = spec.ArchSpec(
        layout=layout
    )

    @move
    def main():
        init.fill([spec.get_static_trap(zone_id="left_traps")])
        # Add some movement operations here

        controls = spec.get_static_trap(zone_id="controls_0")
        targets = spec.get_static_trap(zone_id="targets_0")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_1")
        targets = spec.get_static_trap(zone_id="targets_1")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_2")
        targets = spec.get_static_trap(zone_id="targets_2")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_3")
        targets = spec.get_static_trap(zone_id="targets_3")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_4")
        targets = spec.get_static_trap(zone_id="targets_4")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_5")
        targets = spec.get_static_trap(zone_id="targets_5")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_6")
        targets = spec.get_static_trap(zone_id="targets_6")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_7")
        targets = spec.get_static_trap(zone_id="targets_7")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_8")
        targets = spec.get_static_trap(zone_id="targets_8")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_9")
        targets = spec.get_static_trap(zone_id="targets_9")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_10")
        targets = spec.get_static_trap(zone_id="targets_10")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_11")
        targets = spec.get_static_trap(zone_id="targets_11")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_12")
        targets = spec.get_static_trap(zone_id="targets_12")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_13")
        targets = spec.get_static_trap(zone_id="targets_13")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_14")
        targets = spec.get_static_trap(zone_id="targets_14")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_15")
        targets = spec.get_static_trap(zone_id="targets_15")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_16")
        targets = spec.get_static_trap(zone_id="targets_16")
        run_entangle_move_rtor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_17")
        targets = spec.get_static_trap(zone_id="targets_17")
        run_entangle_move_ltor(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_18")
        targets = spec.get_static_trap(zone_id="targets_18")
        run_entangle_move_ltor(controls, targets)

        return measure.measure((left_traps,))

    return main, spec_value

def run_plotter():
    main, spec_value = generate_moves()
    renderer = MatplotlibRenderer()
    PathVisualizer(main.dialects, renderer=renderer, arch_spec=spec_value).run(main, ())


if __name__ == "__main__":
    run_plotter()
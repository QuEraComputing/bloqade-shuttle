from itertools import repeat, chain
from typing import Any, Literal, TypeVar, List


from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, init, measure, schedule, spec

from bloqade.shuttle.prelude import move, tweezer

from bloqade.shuttle.stdlib.layouts.asserts import assert_sorted

from bloqade.shuttle.visualizer import MatplotlibRenderer, PathVisualizer

from bloqade.insight.upstream.shuttle import ShuttleToInsight
from bloqade.insight.interp import AnimationInterpreter
from bloqade.insight.legacy.animate import animate, FieldOfView
from bloqade.insight import kernel
from kirin import ir

import matplotlib.pyplot as plt


def animate_shuttle(
    main: ir.Method,  # entry point of shuttle program
    spec_value: spec.ArchSpec,  # architecture specification
    display_fov: FieldOfView | None = None,
    dilation_rate: float = 0.05,
    fps: int = 30,
    gate_display_dilation: float = 1.0,
    fig_args={},
    save_mpeg: bool = False,
    filename: str = "vqpu_animation",
    start_block: int = 0,
    n_blocks: int | None = None,
):

    def get_fov(spec: spec.Layout):
        x_min = float("inf")
        x_max = float("-inf")
        y_min = float("inf")
        y_max = float("-inf")
        for zone in chain(spec.static_traps.values(), spec.special_grid.values()):
            x_bounds = zone.x_bounds()
            y_bounds = zone.y_bounds()
            if x_bounds[0] is not None:
                x_min = min(x_min, x_bounds[0])
            if x_bounds[1] is not None:
                x_max = max(x_max, x_bounds[1])
            if y_bounds[0] is not None:
                y_min = min(y_min, y_bounds[0])
            if y_bounds[1] is not None:
                y_max = max(y_max, y_bounds[1])

        return FieldOfView(x_min - 10, x_max + 10, y_min - 10, y_max + 10)

    if display_fov is None:
        display_fov = get_fov(spec_value.layout)

    new_main = main.similar(kernel.union(move))
    ShuttleToInsight(move.union(kernel), 1, spec_value)(new_main)
    timeline = AnimationInterpreter(kernel).get_timeline(new_main, ())
    return animate(
        timeline,
        display_fov=display_fov,
        dilation_rate=dilation_rate,
        fps=fps,
        gate_display_dilation=gate_display_dilation,
        fig_args=fig_args,
        save_mpeg=save_mpeg,
        filename=filename,
        start_block=start_block,
        n_blocks=n_blocks,
    )

# Define type variables for generic programming
NumX = TypeVar('NumX', bound=int)
NumY = TypeVar('NumY', bound=int)

@tweezer
def interzone_move(
    storage_grid: grid.Grid[Any, Any],
    entangling_grid: grid.Grid[Any, Any],
    left:bool
):

    start_x = grid.get_xpos(storage_grid)
    start_y = grid.get_ypos(storage_grid)

    end_x = grid.get_xpos(entangling_grid)
    end_y = grid.get_ypos(entangling_grid)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    if left:
        shift = 3
    else:
        shift = -3

    if start_y[0] > end_y[0]:
        shift_y = 5
    else:
        shift_y = -5

    mid_1 = grid.shift(pos_1, shift, 0)
    mid_2 = grid.shift(pos_2, -3, 0)
    mid_3 = grid.shift(pos_2, start_x[0] - end_x[0] + shift, shift_y)
    mid_4 = grid.shift(pos_2,0,shift_y)

    action.set_loc(pos_1)
    action.turn_on(action.ALL, action.ALL)
    action.move(mid_1)

    if ((start_x[0] - end_x[0]) > -7) and ((start_x[0] - end_x[0]) < 7):
        action.move(mid_2)
    else:
        action.move(mid_3)
        action.move(mid_4)

    action.move(pos_2)

@tweezer
def entangle_move_ltor(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):

    start_x = grid.get_xpos(controls)
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, 2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    if start_y[0] < end_y[0]:
        # moving up
        y_shift = 5
    else:
        # moving down
        y_shift = -5

    if start_y == end_y:
        action.set_loc(pos_1)
        action.turn_on(action.ALL, action.ALL)
        action.move(pos_2)
    elif start_y[0] - end_y[0] in [-10,10]:
        mid_1 = grid.shift(pos_1, 0, y_shift)
        mid_2 = grid.shift(pos_1, 2, y_shift)

        action.set_loc(pos_1)
        action.turn_on(action.ALL, action.ALL)
        action.move(mid_1)
        action.move(mid_2)
        action.move(pos_2)
    else:
        mid_1 = grid.shift(pos_1, 0, y_shift)
        mid_2 = grid.shift(pos_1, 6, y_shift)
        mid_3 = grid.shift(pos_2, 4, 0)

        action.set_loc(pos_1)
        action.turn_on(action.ALL, action.ALL)
        action.move(mid_1)
        action.move(mid_2)
        action.move(mid_3)
        action.move(pos_2)

@tweezer
def entangle_move_ltoaom(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):

    start_x = grid.get_xpos(controls)
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, -2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    if start_y == end_y:
        action.set_loc(pos_1)
        action.turn_on(action.ALL, action.ALL)
        action.move(pos_2)
    else:
        if start_y[0] < end_y[0]:
            # moving up
            y_shift = 5
        else:
            # moving down
            y_shift = -5

        mid_1 = grid.shift(pos_1, 0, y_shift)
        mid_2 = grid.shift(pos_1, -4, y_shift)
        mid_3 = grid.shift(pos_2, -2, 0)

        action.set_loc(pos_1)
        action.turn_on(action.ALL, action.ALL)
        action.move(mid_1)
        action.move(mid_2)
        action.move(mid_3)
        action.move(pos_2)

@tweezer
def entangle_move_rtor(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):

    start_x = grid.get_xpos(grid.shift(controls, 2, 0))
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, 2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    mid_1 = grid.shift(pos_1, 0, 5)
    mid_2 = grid.shift(pos_2, 0, 5)

    action.set_loc(pos_1)
    action.turn_on(action.ALL, action.ALL)
    action.move(mid_1)
    action.move(mid_2)
    action.move(pos_2)

@tweezer
def entangle_move_rtoaom(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):

    start_x = grid.get_xpos(grid.shift(controls, 2, 0))
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(grid.shift(targets, -2, 0))
    end_y = grid.get_ypos(targets)

    pos_1 = grid.from_positions(start_x, start_y)
    pos_2 = grid.from_positions(end_x, end_y)

    mid_1 = grid.shift(pos_1, 0, 5)
    mid_2 = grid.shift(pos_2, 0, 5)

    action.set_loc(pos_1)
    action.turn_on(action.ALL, action.ALL)
    action.move(mid_1)
    action.move(mid_2)
    action.move(pos_2)

@move
def run_interzone_move(
    storage_grid: grid.Grid[Any, Any],
    entangling_grid: grid.Grid[Any, Any],
    left:bool
):
    xtones = ilist.range(len(grid.get_xpos(storage_grid)))
    ytones = ilist.range(len(grid.get_ypos(storage_grid)))

    dtask = schedule.device_fn(interzone_move, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(storage_grid, entangling_grid, left)
    rev_dtask(storage_grid, entangling_grid, left)

@move
def run_entangle_move_ltor(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):
    xtones = ilist.range(len(grid.get_xpos(controls)))
    ytones = ilist.range(len(grid.get_ypos(controls)))

    dtask = schedule.device_fn(entangle_move_ltor, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

@move
def run_entangle_move_ltoaom(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):
    xtones = ilist.range(len(grid.get_xpos(controls)))
    ytones = ilist.range(len(grid.get_ypos(controls)))

    dtask = schedule.device_fn(entangle_move_ltoaom, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

@move
def run_entangle_move_rtor(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):
    xtones = ilist.range(len(grid.get_xpos(controls)))
    ytones = ilist.range(len(grid.get_ypos(controls)))

    dtask = schedule.device_fn(entangle_move_rtor, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

@move
def run_entangle_move_rtoaom(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):
    xtones = ilist.range(len(grid.get_xpos(controls)))
    ytones = ilist.range(len(grid.get_ypos(controls)))

    dtask = schedule.device_fn(entangle_move_rtoaom, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls, targets)
    # apply_cx(gate_zone)
    rev_dtask(controls, targets)

def generate_moves():

    num_x = 17
    num_y = 5
    column_spacing = 8.0
    row_spacing = 10.0
    gate_spacing = 2.0 #space between atoms for CZ gate.

    x_spacing = sum(repeat((gate_spacing, column_spacing), num_x - 1), ()) + (gate_spacing,)
    y_spacing = tuple(repeat(row_spacing, num_y - 1))
    all_entangling_zone_traps = grid.Grid(x_spacing, y_spacing, -81.0, -20.0) # offset to center the grid such that 0,0 is the middle of the AOD.
    left_trap_x_indices = ilist.IList(range(0, num_x * 2, 2))
    right_trap_x_indices = ilist.IList(range(1, num_x * 2, 2))
    all_y_indices = ilist.IList(range(num_y))
    left_traps = all_entangling_zone_traps.get_view(left_trap_x_indices, all_y_indices)
    right_traps = all_entangling_zone_traps.get_view(right_trap_x_indices, all_y_indices)

    aom_sites = left_traps.shift(-2,0)

    reservoir_ally_width = 6.0
    reservoir_column_spacing = column_spacing+gate_spacing-reservoir_ally_width
    reservoir_row_spacing = 4.0
    num_reservoir_rows = 19

    reservoir_x_spacing = sum(repeat((reservoir_ally_width, reservoir_column_spacing), num_x - 1), ()) + (reservoir_ally_width,)
    reservoir_y_spacing = tuple(repeat(reservoir_row_spacing, num_reservoir_rows - 1))

    top_reservoir = grid.Grid(reservoir_x_spacing, reservoir_y_spacing, -81.0 - reservoir_ally_width, row_spacing * 3)
    bottom_reservoir = grid.Grid(reservoir_x_spacing, reservoir_y_spacing, -81.0 - reservoir_ally_width, -3.0 * row_spacing - reservoir_row_spacing * (num_reservoir_rows-1))

    SL0_block_x_indices = ilist.IList(range(4,4+7*2,2))
    SL0_block_y_indices = ilist.IList(range(8,8+5*2,2))
    SL0_block_traps = top_reservoir.get_view(SL0_block_x_indices, SL0_block_y_indices)

    SR0_block_x_indices = ilist.IList(range(5, 5 + 7 * 2, 2))
    SR0_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SR0_block_traps = top_reservoir.get_view(SR0_block_x_indices, SR0_block_y_indices)

    SL1_block_x_indices = ilist.IList(range(4 + 7*2, 4 + 7*2 + 7 * 2, 2))
    SL1_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SL1_block_traps = top_reservoir.get_view(SL1_block_x_indices, SL1_block_y_indices)

    SR1_block_x_indices = ilist.IList(range(5 + 7*2, 5 + 7*2 + 7 * 2, 2))
    SR1_block_y_indices = ilist.IList(range(8, 8 + 5 * 2, 2))
    SR1_block_traps = top_reservoir.get_view(SR1_block_x_indices, SR1_block_y_indices)

    ML0_block_x_indices = ilist.IList(range(4, 4 + 7 * 2, 2))
    ML0_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    ML0_block_traps = bottom_reservoir.get_view(ML0_block_x_indices, ML0_block_y_indices)

    MR0_block_x_indices = ilist.IList(range(5, 5 + 7 * 2, 2))
    MR0_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    MR0_block_traps = bottom_reservoir.get_view(MR0_block_x_indices, MR0_block_y_indices)

    ML1_block_x_indices = ilist.IList(range(4 + 7 * 2, 4 + 7 * 2 + 7 * 2, 2))
    ML1_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    ML1_block_traps = bottom_reservoir.get_view(ML1_block_x_indices, ML1_block_y_indices)

    MR1_block_x_indices = ilist.IList(range(5 + 7 * 2, 5 + 7 * 2 + 7 * 2, 2))
    MR1_block_y_indices = ilist.IList(range(2, 2 + 5 * 2, 2))
    MR1_block_traps = bottom_reservoir.get_view(MR1_block_x_indices, MR1_block_y_indices)

    G0_block_x_indices = ilist.IList(range(2, 2+7))
    GL0_block_traps = left_traps.get_view(G0_block_x_indices, all_y_indices)
    GR0_block_traps = right_traps.get_view(G0_block_x_indices, all_y_indices)

    G1_block_x_indices = ilist.IList(range(2 + 7, 2 + 7 + 7))
    GL1_block_traps = left_traps.get_view(G1_block_x_indices, all_y_indices)
    GR1_block_traps = right_traps.get_view(G1_block_x_indices, all_y_indices)

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

    logical_rows = 5
    logical_cols = 2

    home_x_indices = {
        logical_q_idx: ilist.IList([(q_idx % 14)+2 for q_idx in range(logical_q_idx * 7, logical_q_idx * 7 + 7)]) for
        logical_q_idx in range(int(logical_cols * logical_rows))
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
        fillable=set(["GL0_block","GL1_block","SL0_block","SR0_block","SL1_block","SR1_block", "ML0_block","MR0_block","ML1_block","MR1_block"]),
        has_cz=set(["traps"]),
        has_local=set(["left_traps"]),
        special_grid ={"aom_sites": aom_sites}
    )

    # layout.show()

    spec_value = spec.ArchSpec(
        layout=layout
    )

    @move
    def main():
        init.fill([spec.get_static_trap(zone_id="SL0_block"), spec.get_static_trap(zone_id="SR0_block"),spec.get_static_trap(zone_id="SL1_block"), spec.get_static_trap(zone_id="SR1_block"), spec.get_static_trap(zone_id="ML0_block"), spec.get_static_trap(zone_id="MR0_block"),spec.get_static_trap(zone_id="ML1_block"), spec.get_static_trap(zone_id="MR1_block")])
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

        controls = spec.get_static_trap(zone_id="SL0_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="SR0_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="SL1_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="SR1_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="SL0_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="SR0_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="SL1_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="SR1_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="ML0_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="MR0_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="ML1_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="MR1_block")
        targets = spec.get_static_trap(zone_id="GL0_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="ML0_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="MR0_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, False)

        controls = spec.get_static_trap(zone_id="ML1_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, True)

        controls = spec.get_static_trap(zone_id="MR1_block")
        targets = spec.get_static_trap(zone_id="GL1_block")
        run_interzone_move(controls, targets, False)
        #
        controls = spec.get_static_trap(zone_id="controls_0")
        targets = spec.get_static_trap(zone_id="targets_0")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_1")
        targets = spec.get_static_trap(zone_id="targets_1")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_2")
        targets = spec.get_static_trap(zone_id="targets_2")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_3")
        targets = spec.get_static_trap(zone_id="targets_3")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_4")
        targets = spec.get_static_trap(zone_id="targets_4")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_5")
        targets = spec.get_static_trap(zone_id="targets_5")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_6")
        targets = spec.get_static_trap(zone_id="targets_6")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_7")
        targets = spec.get_static_trap(zone_id="targets_7")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_8")
        targets = spec.get_static_trap(zone_id="targets_8")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_9")
        targets = spec.get_static_trap(zone_id="targets_9")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_10")
        targets = spec.get_static_trap(zone_id="targets_10")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_11")
        targets = spec.get_static_trap(zone_id="targets_11")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_12")
        targets = spec.get_static_trap(zone_id="targets_12")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_13")
        targets = spec.get_static_trap(zone_id="targets_13")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_14")
        targets = spec.get_static_trap(zone_id="targets_14")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_15")
        targets = spec.get_static_trap(zone_id="targets_15")
        run_entangle_move_ltoaom(controls, targets)

        controls = spec.get_static_trap(zone_id="controls_16")
        targets = spec.get_static_trap(zone_id="targets_16")
        run_entangle_move_rtoaom(controls, targets)


    return main, spec_value

def run_plotter():
    main, spec_value = generate_moves()
    renderer = MatplotlibRenderer()
    PathVisualizer(main.dialects, renderer=renderer, arch_spec=spec_value).run(main, ())

    # ani = animate_shuttle(main, spec_value, fps = 30, dilation_rate=0.015)
    #
    # ani.save("gate_zone_logical_moves.mp4", writer="ffmpeg", fps=30, dpi=200)

    plt.show()


if __name__ == "__main__":
    run_plotter()
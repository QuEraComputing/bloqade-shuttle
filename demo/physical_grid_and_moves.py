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
    # new_main.print(hint="const")
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
def row_move_impl(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):

    start_x = grid.get_xpos(controls)
    start_y = grid.get_ypos(controls)

    end_x = grid.get_xpos(targets)
    end_y = grid.get_ypos(targets)

    mid_1 = grid.shift(controls, 0, 5)
    mid_2 = grid.shift(controls, 4 + (end_x[0]-start_x[0]), 5)
    mid_3 = grid.shift(targets, 4, 0)

    action.set_loc(controls)
    action.turn_on(action.ALL, action.ALL)
    action.move(mid_1)
    action.move(mid_2)
    action.move(mid_3)
    action.move(targets)

@move
def run_move(
    controls: grid.Grid[Any, Any],
    targets: grid.Grid[Any, Any],
):
    xtones = ilist.range(len(grid.get_xpos(controls)))
    ytones = ilist.range(len(grid.get_ypos(controls)))

    dtask = schedule.device_fn(row_move_impl, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(controls,targets)
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

    SL_block_x_indices = ilist.IList(range(2,2+8*2,2))
    SL_block_y_indices = ilist.IList(range(8,8+4*2,2))
    SL_block_traps = top_reservoir.get_view(SL_block_x_indices, SL_block_y_indices)

    SR_block_x_indices = ilist.IList(range(3,3+8*2,2))
    SR_block_y_indices = ilist.IList(range(8,8+4*2,2))
    SR_block_traps = top_reservoir.get_view(SR_block_x_indices, SR_block_y_indices)

    ML_block_x_indices = ilist.IList(range(2,2+8*2,2))
    ML_block_y_indices = ilist.IList(range(2,2+4*2,2))
    ML_block_traps = top_reservoir.get_view(ML_block_x_indices, ML_block_y_indices)

    MR_block_x_indices = ilist.IList(range(3,3+8*2,2))
    MR_block_y_indices = ilist.IList(range(2,2+4*2,2))
    MR_block_traps = top_reservoir.get_view(MR_block_x_indices, MR_block_y_indices)

    G_block_x_indices  = ilist.IList(range(1,1+16))
    G_block_y_indices = all_y_indices[:-1]
    GL_block_traps = left_traps.get_view(G_block_x_indices, G_block_y_indices)
    GR_block_traps = right_traps.get_view(G_block_x_indices, G_block_y_indices)

    evenL_rows = GL_block_traps.get_view(list(range(0,16)), [0,2])

    oddR_rows = GR_block_traps.get_view(list(range(0,16)), [1,3])

    evenL_cols = GL_block_traps.get_view(range(0,16,2), range(4))
    oddR_cols = GR_block_traps.get_view(range(1,16,2), range(4))

    first2L_rows =GL_block_traps.get_view(range(16), [0, 1])
    second2R_rows = GR_block_traps.get_view(range(16), [2, 3])

    first2L_cols = GL_block_traps.get_view([0,1,4,5,8,9,12,13], range(4))
    second2R_cols = GR_block_traps.get_view([2,3,6,7,10,11,14,15], range(4))

    fourL_block_02 = GL_block_traps.get_view([0,1,2,3,8,9,10,11], range(4))
    fourR_block_13 = GR_block_traps.get_view([4,5,6,7,12,13,14,15], range(4))

    fourL_block_01 = GL_block_traps.get_view(range(8), range(4))
    fourR_block_23 = GR_block_traps.get_view(range(8,16), range(4))

    secondL_row = GL_block_traps.get_view(range(16), [1])
    thirdR_row = GR_block_traps.get_view(range(16), [2])

    fourthL_row = GL_block_traps.get_view(range(16), [3])
    firstR_row = GR_block_traps.get_view(range(16), [0])

    secondL_cols = GL_block_traps.get_view(range(1,16,4), range(4))
    thirdR_cols = GR_block_traps.get_view(range(2,16,4), range(4))

    fourthL_cols = GL_block_traps.get_view(range(3,16,4), range(4))
    firstR_cols = GR_block_traps.get_view(range(0,16,4), range(4))

    fourL_block_1 = GL_block_traps.get_view(range(4,8), range(4))
    fourR_block_2 = GR_block_traps.get_view(range(8,12), range(4))

    fourL_block_3 = GL_block_traps.get_view(range(12,16), range(4))
    fourR_block_0 = GR_block_traps.get_view(range(4), range(4))


    static_traps = {
        "traps": all_entangling_zone_traps,
        "left_traps": left_traps,
        "right_traps": right_traps,
        "top_reservoir": top_reservoir,
        "bottom_reservoir": bottom_reservoir,
        "SL_block": SL_block_traps,
        "SR_block": SR_block_traps,
        "ML_block": ML_block_traps,
        "MR_block": MR_block_traps,
        "GL_block": GL_block_traps,
        "GR_block": GR_block_traps,
        "evenL_rows": evenL_rows,
        "oddR_rows": oddR_rows,
        "evenL_cols": evenL_cols,
        "oddR_cols": oddR_cols,
        "first2L_rows": first2L_rows,
        "second2R_rows": second2R_rows,
        "first2L_cols": first2L_cols,
        "second2R_cols": second2R_cols,
        "fourL_block_02": fourL_block_02,
        "fourR_block_13": fourR_block_13,
        'fourL_block_01': fourL_block_01,
        'fourR_block_23': fourR_block_23,
        'secondL_row': secondL_row,
        'thirdR_row': thirdR_row,
        'fourthL_row': fourthL_row,
        'firstR_row': firstR_row,
        'secondL_cols': secondL_cols,
        'thirdR_cols': thirdR_cols,
        'fourthL_cols': fourthL_cols,
        'firstR_clos': firstR_cols,
        'fourL_block_1': fourL_block_1,
        'fourR_block_2': fourR_block_2,
        'fourL_block_3': fourL_block_3,
        'fourR_block_0': fourR_block_0,
    }

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
        init.fill([spec.get_static_trap(zone_id="left_traps")])
        # Add some movement operations here

        #Start with hypercube moves

        controls = spec.get_static_trap(zone_id="evenL_rows")
        targets = spec.get_static_trap(zone_id="oddR_rows")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="evenL_cols")
        targets = spec.get_static_trap(zone_id="oddR_cols")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="first2L_rows")
        targets = spec.get_static_trap(zone_id="second2R_rows")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="first2L_cols")
        targets = spec.get_static_trap(zone_id="second2R_cols")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourL_block_02")
        targets = spec.get_static_trap(zone_id="fourR_block_13")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourL_block_01")
        targets = spec.get_static_trap(zone_id="fourR_block_23")
        run_move(controls, targets)

        # Addtional moves to achieve 4x4x4 NN

        controls = spec.get_static_trap(zone_id="secondL_row")
        targets = spec.get_static_trap(zone_id="thirdR_row")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourthL_row")
        targets = spec.get_static_trap(zone_id="firstR_row")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="secondL_cols")
        targets = spec.get_static_trap(zone_id="thirdR_cols")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourthL_cols")
        targets = spec.get_static_trap(zone_id="firstR_clos")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourL_block_1")
        targets = spec.get_static_trap(zone_id="fourR_block_2")
        run_move(controls, targets)

        controls = spec.get_static_trap(zone_id="fourL_block_3")
        targets = spec.get_static_trap(zone_id="fourR_block_0")
        run_move(controls, targets)

        # Storage zone moves undone.


    return main, spec_value

def run_plotter():
    main, spec_value = generate_moves()
    renderer = MatplotlibRenderer()
    PathVisualizer(main.dialects, renderer=renderer, arch_spec=spec_value).run(main, ())

    # ani = animate_shuttle(main, spec_value)
    #
    # ani.save("gate_zone_physical_4x4x4_moves.mp4", writer="ffmpeg", fps=45, dpi=200)
    #
    # plt.show()


if __name__ == "__main__":
    run_plotter()
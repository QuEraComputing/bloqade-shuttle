import math
from typing import Any, Literal, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, init, measure, schedule
from bloqade.shuttle.passes.fold import AggressiveUnroll
from bloqade.shuttle.prelude import move, tweezer

NMove = TypeVar("NMove")


@tweezer
def entangle_move(
    mem_zone: grid.Grid[Any, Literal[1]],
    gate_zone: grid.Grid[NMove, Literal[2]],
    ctrl_ids: ilist.IList[int, NMove],
    qarg_ids: ilist.IList[int, NMove],
    gate_ids: ilist.IList[int, NMove],
):

    mem_y = grid.get_ypos(mem_zone)[0]
    ctrl_start = grid.get_xpos(grid.sub_grid(mem_zone, ctrl_ids, [0]))
    qarg_start = grid.get_xpos(grid.sub_grid(mem_zone, qarg_ids, [0]))

    pos_1 = grid.from_positions(ctrl_start, [mem_y, mem_y])
    pos_2 = grid.shift(grid.from_positions(ctrl_start, [mem_y - 4.0, mem_y]), 2.0, 0.0)
    pos_3 = grid.from_positions(qarg_start, [mem_y - 4.0, mem_y])
    gate_pos = grid.sub_grid(gate_zone, gate_ids, [0, 1])

    action.set_loc(pos_1)
    action.turn_on(action.ALL, [0])
    action.move(pos_2)
    action.move(pos_3)
    action.turn_on([], [1])
    action.move(gate_pos)


@move
def apply_h(zone: grid.Grid[Any, Any]):
    # TODO: This is wrong and needs to be fixed.
    gate.global_r(math.pi / 2.0, -math.pi / 2.0)
    gate.local_rz(math.pi / 2.0, zone)
    gate.global_r(0.0, -math.pi / 2.0)


@move
def apply_cx(gate_zone: grid.Grid[Any, Any]):
    # TODO: This is wrong and needs to be fixed.
    gate.global_r(0.0, math.pi)
    gate.top_hat_cz(gate_zone)
    gate.global_r(0.0, -math.pi)


@move
def run_entangle_move(
    mem_zone: grid.Grid[Any, Literal[1]],
    gate_zone: grid.Grid[Any, Literal[2]],
    ctrl_ids: ilist.IList[int, NMove],
    qarg_ids: ilist.IList[int, NMove],
    gate_ids: ilist.IList[int, NMove],
):

    num = len(ctrl_ids)
    xtones = ilist.range(num)
    ytones = [0, 1]

    dtask = schedule.device_fn(entangle_move, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    dtask(mem_zone, gate_zone, ctrl_ids, qarg_ids, gate_ids)
    apply_cx(gate_zone)
    rev_dtask(mem_zone, gate_zone, ctrl_ids, qarg_ids, gate_ids)


N = TypeVar("N")


@move
def ghz_prep_steps(
    qubit_ids: ilist.IList[int, N],
    gate: grid.Grid[Any, Literal[2]],
    mem: grid.Grid[Any, Literal[1]],
):

    n_qubits = len(qubit_ids)
    gate_shape = grid.shape(gate)
    gate_width = gate_shape[0]

    jobs = []
    # calculate the qubits in each layer then split up into groups based on the size of the gate
    for depth in range(n_qubits):
        step = n_qubits // (2**depth)
        half_step = step // 2
        if half_step > 0:
            ctrl_qubits = qubit_ids[:-half_step:half_step]
            qarg_qubits = qubit_ids[half_step::half_step]

            num_gates = len(ctrl_qubits)
            num_substeps = num_gates // gate_width + 1

            for i in range(num_substeps):
                start = i * gate_width
                stop = start + gate_width

                if stop > num_gates:
                    stop = num_gates

                if stop > start:
                    ctrl_ids = ctrl_qubits[start:stop]
                    qarg_ids = qarg_qubits[start:stop]
                    gate_ids = ilist.range(stop - start)
                    jobs = jobs + [(ctrl_ids, qarg_ids, gate_ids)]

    for i in range(len(jobs)):
        ctrl_ids = jobs[i][0]
        qarg_ids = jobs[i][1]
        gate_ids = jobs[i][2]
        run_entangle_move(mem, gate, ctrl_ids, qarg_ids, gate_ids)


def run_ghz():
    spacing = 4
    num_sites = 32
    mem = grid.Grid.from_positions(
        list(map(float, range(0, spacing * num_sites, spacing))), [20.0]
    )

    num_gate = int(mem.width // 20) + 1
    gate = grid.Grid.from_positions(
        list(map(float, range(0, num_gate * 20, 20))), [0.0, 3.0]
    )

    mem_bounds = mem.x_bounds()
    assert mem_bounds[0] is not None
    assert mem_bounds[1] is not None

    mid_mem = (mem.x_positions[0] + mem.x_positions[-1]) / 2
    mid_gate = (gate.x_positions[0] + gate.x_positions[-1]) / 2

    gate_shift = mid_mem - mid_gate

    gate = gate.shift(gate_shift, 0.0)

    @move
    def main():
        init.fill([mem])
        ghz_prep_steps([1, 2, 4, 5, 7, 9, 14, 28, 29, 32], gate, mem)  # type: ignore
        return measure.measure((mem,))

    return main


def test_fold():
    main = run_ghz()
    AggressiveUnroll(main.dialects).fixpoint(main)
    main.print()


if __name__ == "__main__":
    test_fold()

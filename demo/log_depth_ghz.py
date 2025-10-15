import math
from typing import Any, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, init, schedule, spec
from bloqade.shuttle.prelude import move, tweezer
from bloqade.shuttle.visualizer import PathVisualizer

NMove = TypeVar("NMove")


@tweezer
def entangle_move(
    ctrl_ids: ilist.IList[int, NMove],
    qarg_ids: ilist.IList[int, NMove],
    gate_ids: ilist.IList[int, NMove],
):

    mem_zone = spec.get_static_trap(zone_id="mem")
    gate_zone = spec.get_special_grid(grid_id="gate")

    mem_y = grid.get_ypos(mem_zone)[0]
    ctrl_start = grid.get_xpos(mem_zone[ctrl_ids, 0])
    qarg_start = grid.get_xpos(mem_zone[qarg_ids, 0])

    pos_1 = grid.from_positions(ctrl_start, [mem_y, mem_y + 4.0])
    pos_2 = grid.shift(pos_1, 0.0, -4.0)
    pos_3 = grid.from_positions(qarg_start, grid.get_ypos(pos_2))
    pos_4 = grid.shift(pos_3, 0.0, -4.0)
    gate_pos = gate_zone[gate_ids, :]

    action.set_loc(pos_1)
    action.turn_on(action.ALL, [0])
    action.move(pos_2)
    action.move(pos_3)
    action.turn_on([], [1])
    action.move(pos_4)
    action.move(gate_pos)


@move
def apply_h(zone: grid.Grid[Any, Any]):
    # TODO: This is wrong and needs to be fixed.
    gate.global_r(math.pi / 2.0, -math.pi / 2.0)
    gate.local_rz(math.pi / 2.0, zone)
    gate.global_r(0.0, -math.pi / 2.0)


@move
def run_entangle_move(
    ctrl_ids: ilist.IList[int, NMove],
    qarg_ids: ilist.IList[int, NMove],
    gate_ids: ilist.IList[int, NMove],
):

    gate_zone = spec.get_special_grid(grid_id="gate")
    mem_zone = spec.get_static_trap(zone_id="mem")

    num = len(ctrl_ids)
    xtones = ilist.range(num)
    ytones = [0, 1]

    dtask = schedule.device_fn(entangle_move, xtones, ytones)
    rev_dtask = schedule.reverse(dtask)

    gate.local_r(0.0, math.pi, mem_zone[qarg_ids, 0])
    dtask(ctrl_ids, qarg_ids, gate_ids)
    gate.top_hat_cz(gate_zone)
    rev_dtask(ctrl_ids, qarg_ids, gate_ids)
    gate.local_r(0.0, -math.pi, mem_zone[qarg_ids, 0])


N = TypeVar("N")


@move
def get_layers(qubits: ilist.IList[int, N]):
    n_qubits = len(qubits)
    layers = []
    prepared = [qubits[0]]

    for depth in range(n_qubits):
        if len(prepared) < n_qubits:
            remaining = qubits[len(prepared) :]
            ctrls = []
            qargs = []
            for prev_idx in range(len(prepared)):
                if prev_idx < len(remaining):
                    ctrls = ctrls + [prepared[prev_idx]]
                    qargs = qargs + [remaining[prev_idx]]

            layers = layers + [(ctrls, qargs)]
            prepared = prepared + qargs

    return layers


@move
def ghz_prep_steps(
    qubit_ids: ilist.IList[int, N],
    gate_width: int,
):
    jobs = []
    layers = get_layers(qubit_ids)
    mid = gate_width // 2
    for i in range(len(layers)):
        ctrl_ids = layers[i][0]
        qarg_ids = layers[i][1]
        n_gates = len(ctrl_ids)
        num_groups = (n_gates + gate_width - 1) // gate_width

        for group in range(num_groups):
            start = group * gate_width
            end = start + gate_width
            if end > n_gates:
                end = n_gates

            layer_size = end - start
            gate_start = mid - (layer_size // 2)
            gate_end = gate_start + layer_size

            jobs = jobs + [
                (ctrl_ids[start:end], qarg_ids[start:end], range(gate_start, gate_end))
            ]

    return jobs


@move
def run_prep_steps(
    qubit_ids: ilist.IList[int, N],
):

    gate_zone = spec.get_special_grid(grid_id="gate")
    mem_zone = spec.get_static_trap(zone_id="mem")
    gate_shape = grid.shape(gate_zone)
    gate_width = gate_shape[0]

    jobs = ghz_prep_steps(qubit_ids, gate_width)
    apply_h(mem_zone[qubit_ids[0], 0])
    for i in range(len(jobs)):
        ctrl_ids = jobs[i][0]
        qarg_ids = jobs[i][1]
        gate_ids = jobs[i][2]
        run_entangle_move(ctrl_ids, qarg_ids, gate_ids)


def run_ghz():
    spacing = 4
    num_sites = 32
    mem = grid.Grid.from_positions(
        list(map(float, range(0, spacing * num_sites, spacing))), [20.0]
    )

    num_gate = int(mem.width // 10) + 1
    gate = grid.Grid.from_positions(
        list(map(float, range(0, num_gate * 10, 10))), [0.0, 3.0]
    )

    mem_bounds = mem.x_bounds()
    assert mem_bounds[0] is not None
    assert mem_bounds[1] is not None

    mid_mem = (mem.x_positions[0] + mem.x_positions[-1]) / 2
    mid_gate = (gate.x_positions[0] + gate.x_positions[-1]) / 2

    gate_shift = mid_mem - mid_gate

    gate = gate.shift(gate_shift, 0.0)
    spec_value = spec.ArchSpec(
        layout=spec.Layout(
            static_traps={
                "mem": mem,
            },
            special_grid={
                "gate": gate,
            },
            fillable=set(["mem"]),
            has_cz=set(["gate"]),
            has_local=set(["mem"]),
        )
    )

    @move
    def main():
        init.fill([spec.get_static_trap(zone_id="mem")])
        run_prep_steps([1, 2, 4, 5, 7, 9, 14, 28, 29, 32])  # type: ignore
        # return measure.measure((mem,))

    return main, spec_value


def run_plotter():
    main, spec_value = run_ghz()

    PathVisualizer(main.dialects, arch_spec=spec_value).run(main, args=())


if __name__ == "__main__":
    run_plotter()

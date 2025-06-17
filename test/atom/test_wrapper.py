import bloqade.squin as squin
from bloqade.geometry.dialects import grid

import bloqade.shuttle as qourier


def emit_kernel():

    slm = grid.Grid.from_positions(list(map(float, range(0, 4 * 32, 4))), [20])

    n_gate = int(slm.width // 20) + 1

    gate_slots = grid.Grid.from_positions([0, 3], [0]).repeat(n_gate, 1, 20, 1)
    slm_bounds = slm.x_bounds()
    gate_bounds = gate_slots.x_bounds()
    assert slm_bounds[0] is not None
    assert slm_bounds[1] is not None
    assert gate_bounds[0] is not None
    assert gate_bounds[1] is not None

    slm_mid = (slm_bounds[0] + slm_bounds[1]) / 2
    gate_mid = (gate_bounds[0] + gate_bounds[1]) / 2

    gate_slots = gate_slots.shift(gate_mid - slm_mid, 0)

    @qourier.kernel
    def main():
        qubits = squin.qubit.new(4)
        atoms = qourier.atom.new(slm, qubits)
        ctrls, qargs = qourier.atom.move_next_to(gate_slots, atoms[0::2], atoms[1::2])
        qourier.gate.top_hat_cz(gate_slots)
        results = qourier.atom.measure(ctrls, qubits[::2])
        qourier.atom.reset_position(qargs, qubits[1::2])
        return results

    return main


def test_wrappers():
    ker = emit_kernel()

    assert ker is not None

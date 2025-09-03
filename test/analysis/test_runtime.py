from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import gate, init, measure, spec
from bloqade.shuttle.analysis.runtime import RuntimeAnalysis
from bloqade.shuttle.prelude import move
from bloqade.shuttle.stdlib.waypoints import move_by_waypoints


def test_simple_true():
    @move
    def main():
        i = 2
        init.fill([spec.get_static_trap(zone_id="test")])
        return i

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_simple_false():
    @move
    def main():
        return 1

    assert not RuntimeAnalysis(move).has_quantum_runtime(main)


def test_if_1():
    @move
    def main():
        i = 0
        if i % 2 == 0:
            return measure.measure((spec.get_static_trap(zone_id="test"),))

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_if_2():
    @move
    def main():
        i = 0
        if i % 2 == 0:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_if_3():
    @move
    def main(cond: bool):
        i = 0
        start = spec.get_static_trap(zone_id="test")
        end = grid.shift(start, 1, 0)
        if cond:
            move_by_waypoints(ilist.IList([start, end]))
            i = i + 1
        else:
            return 1

        return i

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_if_4():
    @move
    def main(cond: bool):
        i = 0
        if cond:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i + 2
        else:
            return i + 1

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_if_5():
    @move
    def main(cond: bool):
        i = 0
        if cond:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i + 2
        else:
            i = i + 1

        return i

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_loop_1():
    @move
    def main():
        i = 0
        for i in range(1, 9, 2):
            if i % 2 == 0:
                gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    assert not RuntimeAnalysis(move).has_quantum_runtime(main)


def test_loop_2():
    @move
    def main():
        i = 0
        for i in range(0, 9, 2):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_loop_3():
    @move
    def main():
        i = 0
        for i in range(0, 9, 2):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_subroutine_1():
    @move
    def subroutine():
        gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    @move
    def main():
        i = 0
        subroutine()
        return i

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_subroutine_2():
    @move
    def subroutine(a: int):
        return a + 1

    @move
    def main(i: int):
        return subroutine(i)

    assert not RuntimeAnalysis(move).has_quantum_runtime(main)


def test_lambda_1():
    @move
    def main():
        def inner():
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

        inner()

    assert RuntimeAnalysis(move).has_quantum_runtime(main)


def test_lambda_2():
    @move
    def main(a: int):
        def inner(i: int):
            return i + 1

        return inner(a)

    assert not RuntimeAnalysis(move).has_quantum_runtime(main)


def test_lambda_3():
    @move
    def main(a: int):
        def inner(i: int):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i + 1

        return inner

    assert not RuntimeAnalysis(move).has_quantum_runtime(main)


def test_lambda_4():
    @move
    def subroutine(a: int):
        def inner(i: int):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return a + i

        return inner

    @move
    def main(i: int):
        f = subroutine(i)
        return f(i)

    assert RuntimeAnalysis(move).has_quantum_runtime(main)

from bloqade.shuttle import gate, spec
from bloqade.shuttle.analysis.runtime import RuntimeAnalysis
from bloqade.shuttle.prelude import move


def test_simple_true():
    @move
    def main():
        i = 2
        gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
        return i

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_simple_false():
    @move
    def main():
        return 1

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert not frame.is_quantum


def test_if_1():
    @move
    def main():
        i = 0
        if i % 2 == 0:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_if_2():
    @move
    def main():
        i = 0
        if i % 2 == 0:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_if_3():
    @move
    def main(cond: bool):
        i = 0
        if cond:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            i = i + 1
        else:
            return 1

        return i

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_if_4():
    @move
    def main(cond: bool):
        i = 0
        if cond:
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i + 2
        else:
            return i + 1

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


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

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_loop_1():
    @move
    def main():
        i = 0
        for i in range(1, 9, 2):
            if i % 2 == 0:
                gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert not frame.is_quantum


def test_loop_2():
    @move
    def main():
        i = 0
        for i in range(0, 9, 2):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_loop_3():
    @move
    def main():
        i = 0
        for i in range(0, 9, 2):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_subroutine_1():
    @move
    def subroutine():
        gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

    @move
    def main():
        i = 0
        subroutine()
        return i

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_subroutine_2():
    @move
    def subroutine(a: int):
        return a + 1

    @move
    def main(i: int):
        return subroutine(i)

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert not frame.is_quantum


def test_lambda_1():
    @move
    def main():
        def inner():
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))

        inner()

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum


def test_lambda_2():
    @move
    def main(a: int):
        def inner(i: int):
            return i + 1

        return inner(a)

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert not frame.is_quantum


def test_lambda_3():
    @move
    def main(a: int):
        def inner(i: int):
            gate.top_hat_cz(spec.get_static_trap(zone_id="test"))
            return i + 1

        return inner

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert not frame.is_quantum


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

    analysis = RuntimeAnalysis(move)
    frame, _ = analysis.run_analysis(main)
    assert frame.is_quantum

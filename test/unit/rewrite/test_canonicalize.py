from kirin import ir, rewrite
from kirin.dialects import func

from bloqade.shuttle.rewrite.schedule2path import Canonicalize

from .utils import assert_block_equal, sch


def test_canonicalize_do_nothing():

    callee_1 = ir.TestValue()
    callee_2 = ir.TestValue()
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,)),
                    sch.auto(func.Call(callee_1, (input_1,))),
                ),
                sch.parallel(func.Call(callee_2, (input_2,))),
            )
        ]
    )

    expected_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,)),
                    sch.auto(func.Call(callee_1, (input_1,))),
                ),
                sch.parallel(func.Call(callee_2, (input_2,))),
            )
        ]
    )

    rewrite.Walk(Canonicalize()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)


def test_canonicalize_flatten_auto():

    callee_1 = ir.TestValue()
    callee_2 = ir.TestValue()
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,)),
                    sch.parallel(func.Call(callee_1, (input_1,))),
                ),
                sch.auto(
                    func.Call(callee_2, (input_2,)), func.Call(callee_1, (input_1,))
                ),
            )
        ]
    )

    expected_block = ir.Block(
        [
            sch.auto(
                sch.parallel(
                    func.Call(callee_1, (input_1,)), func.Call(callee_1, (input_1,))
                ),
                func.Call(callee_2, (input_2,)),
                func.Call(callee_1, (input_1,)),
            )
        ]
    )

    rewrite.Walk(Canonicalize()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)

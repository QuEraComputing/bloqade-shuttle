from kirin import ir, rewrite

from bloqade.shuttle.dialects import path, schedule
from bloqade.shuttle.rewrite import schedule2path

from .utils import assert_block_equal, pth, sch


def test_rewrite_no_nesting():
    device_fn = ir.TestValue(schedule.DeviceFunctionType)
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.parallel(
                path.Gen(device_fn, (input_1, input_2)),
                path.Gen(device_fn, (input_2, input_1)),
            )
        ]
    )

    expected_block = ir.Block(
        [
            path1 := path.Gen(device_fn, (input_1, input_2)),
            path2 := path.Gen(device_fn, (input_2, input_1)),
            ppath := pth.parallel(
                path1.result,
                path2.result,
            ),
            path.Play(ppath.result),
        ]
    )

    rewrite.Walk(schedule2path.RewriteScheduleRegion()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)


def test_rewrite_no_nesting_1_level():
    device_fn = ir.TestValue(schedule.DeviceFunctionType)
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()
    input_3 = ir.TestValue()
    input_4 = ir.TestValue()

    test_block = ir.Block(
        [
            sch.parallel(
                sch.auto(
                    path.Gen(device_fn, (input_1,)),
                    sch.parallel(
                        path.Gen(device_fn, (input_2,)),
                        path.Gen(device_fn, (input_3,)),
                    ),
                ),
                sch.auto(path.Gen(device_fn, (input_4,))),
            )
        ]
    )

    expected_block = ir.Block(
        [
            path1 := path.Gen(device_fn, (input_1,)),
            path2 := path.Gen(device_fn, (input_2,)),
            path3 := path.Gen(device_fn, (input_3,)),
            parallel1 := pth.parallel(path2.result, path3.result),
            auto0 := pth.auto(path1.result, parallel1.result),
            path4 := path.Gen(device_fn, (input_4,)),
            auth1 := pth.auto(path4.result),
            ppath := pth.parallel(auto0.result, auth1.result),
            path.Play(ppath.result),
        ]
    )

    rewrite.Walk(schedule2path.RewriteScheduleRegion()).rewrite(test_block)

    assert_block_equal(test_block, expected_block)


if __name__ == "__main__":
    test_rewrite_no_nesting()
    test_rewrite_no_nesting_1_level()
    print("Test passed!")

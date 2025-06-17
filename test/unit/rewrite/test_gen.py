from kirin import ir, rewrite
from kirin.dialects import func, py

from bloqade.shuttle.dialects import path, schedule
from bloqade.shuttle.rewrite import schedule2path

from .utils import assert_block_equal, sch


def test_rewrite_to_device_call_with_play():
    """Test that the rewrite to device call works correctly."""
    # Create a test value for the device function
    device_fn = ir.TestValue(schedule.DeviceFunctionType)
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    # Create a test block with a device function call
    test_block = ir.Block(
        [
            input_1 := py.Constant(1),
            func.Call(
                callee=device_fn,
                inputs=(input_1.result, input_2),
            ),
        ]
    )

    rewrite.Walk(schedule2path.RewriteDeviceCall()).rewrite(test_block)

    expected_block = ir.Block(
        [
            input_1 := py.Constant(1),
            gen_stmt := path.Gen(
                device_fn,
                inputs=(input_1.result, input_2),
            ),
            path.Play(gen_stmt.result),
        ]
    )

    assert_block_equal(test_block, expected_block)


def test_rewrite_to_device_call_without_play():
    """Test that the rewrite to device call works correctly."""
    # Create a test value for the device function
    device_fn = ir.TestValue(schedule.DeviceFunctionType)
    input_1 = ir.TestValue()
    input_2 = ir.TestValue()

    # Create a test block with a device function call
    test_block = ir.Block(
        [
            input_1 := py.Constant(1),
            sch.auto(
                func.Call(
                    callee=device_fn,
                    inputs=(input_1.result, input_2),
                    kwargs=(),
                )
            ),
        ]
    )

    rewrite.Walk(schedule2path.RewriteDeviceCall()).rewrite(test_block)

    expected_block = ir.Block(
        [
            input_1 := py.Constant(1),
            sch.auto(
                path.Gen(
                    device_fn,
                    inputs=(input_1.result, input_2),
                    kwargs=(),
                )
            ),
        ]
    )

    assert_block_equal(test_block, expected_block)

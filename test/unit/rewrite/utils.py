from kirin import ir

from bloqade.shuttle.dialects import path, schedule


def simple_region(*stmts: ir.Statement) -> ir.Region:
    """Create a simple block with the given statements."""
    return ir.Region([ir.Block(stmts)])


def call(callee: ir.SSAValue, inputs: tuple[ir.SSAValue, ...]) -> path.Gen:
    """Create a function call with the given callee and inputs."""
    return path.Gen(callee, inputs, kwargs=())


class sch:

    @classmethod
    def auto(cls, *stmts: ir.Statement) -> schedule.Auto:
        """Create an Auto statement with the given statements."""
        return schedule.Auto(body=simple_region(*stmts))

    @classmethod
    def parallel(cls, *stmts: ir.Statement) -> schedule.Parallel:
        """Create a Parallel statement with the given statements."""
        return schedule.Parallel(body=simple_region(*stmts))


class pth:

    @classmethod
    def auto(cls, *paths: ir.SSAValue) -> path.Auto:
        """Create an Auto statement with the given statements."""
        return path.Auto(paths=paths)

    @classmethod
    def parallel(cls, *paths: ir.SSAValue) -> path.Parallel:
        """Create a Parallel statement with the given statements."""
        return path.Parallel(paths=paths)


def assert_block_equal(actual: ir.Block, expected: ir.Block):
    """Assert that two blocks are structurally equal."""
    try:
        assert actual.is_structurally_equal(expected)
    except AssertionError as e:
        actual.print()
        expected.print()
        raise e

from bloqade.geometry.dialects import grid
from bloqade.insight.dialects import trajectory
from bloqade.squin import qubit
from bloqade.test_utils import assert_nodes
from kirin import ir, rewrite, types
from kirin.analysis import const
from kirin.dialects import cf, ilist, py

from bloqade.shuttle.dialects import init
from bloqade.shuttle.passes import path2insight


def test_rewrite_fill():

    locations = ir.TestValue()

    locations_value = ilist.IList(
        [
            grid.Grid.from_positions([0, 1], [0, 1]),
            grid.Grid.from_positions([2, 3], [2, 3]),
        ]
    )

    locations.hints["const"] = const.Value(locations_value)

    test_region = ir.Region(test_block := ir.Block())
    arg = test_block.args.append_from(types.Float, name="argument")

    test_block.stmts.append(const_stmt := py.Constant(10.0))
    test_block.stmts.append(
        init.Fill(
            locations,
        )
    )
    test_block.stmts.append(py.Mult(arg, const_stmt.result))

    expected_region = ir.Region([entry_block := ir.Block(), next_block := ir.Block()])

    arg = entry_block.args.append_from(types.Float, name="argument")

    entry_block.stmts.append(const_stmt := py.Constant(10.0))
    entry_block.stmts.append(num_qubits_stmt := py.Constant(8))
    entry_block.stmts.append(qubits_stmt := qubit.New(num_qubits_stmt.result))
    entry_block.stmts.append(
        positions_stmt := py.Constant(
            ilist.IList(
                [(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3)]
            )
        )
    )
    entry_block.stmts.append(
        insight_init := trajectory.Initialize(qubits_stmt.result, positions_stmt.result)
    )

    entry_block.stmts.append(cf.Branch((insight_init.state,), successor=next_block))
    next_block.args.append_from(trajectory.AtomStateType, name="atom_state")
    next_block.stmts.append(py.Mult(arg, const_stmt.result))

    rewrite.Walk(path2insight.PathToInsightRule()).rewrite(test_region)

    assert_nodes(test_region, expected_region)


if __name__ == "__main__":
    test_rewrite_fill()
    print("Test passed successfully.")

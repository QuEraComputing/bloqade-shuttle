from bloqade.geometry.dialects import grid
from bloqade.insight.dialects import trajectory
from bloqade.squin import qubit
from bloqade.test_utils import assert_nodes
from kirin import ir, rewrite, types
from kirin.analysis import const
from kirin.dialects import cf, ilist, py

from bloqade.shuttle.codegen import taskgen
from bloqade.shuttle.dialects import init, path
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


def generate_path():
    x_tones = ilist.IList([3, 4, 5])
    y_tones = ilist.IList([0, 1, 2])

    pos_0 = grid.Grid.from_positions([0, 1, 2], [0, 1, 2])
    pos_1 = grid.Grid.from_positions([3, 4, 5], [3, 4, 5])
    pos_2 = grid.Grid.from_positions([6, 7, 8], [6, 7, 8])
    pos_3 = grid.Grid.from_positions([9, 10, 11], [9, 10, 11])

    actions = [
        taskgen.WayPointsAction([pos_0]),
        taskgen.TurnOnYSliceAction(ilist.IList([0]), slice(None)),
        taskgen.WayPointsAction([pos_0, pos_1]),
        taskgen.TurnOnYSliceAction(ilist.IList([1]), slice(None)),
        taskgen.WayPointsAction([pos_1, pos_2]),
        taskgen.TurnOffXYAction(ilist.IList([]), ilist.IList([0])),
        taskgen.WayPointsAction([pos_2, pos_3]),
    ]

    trajectories = [
        trajectory.Trajectory(
            waypoints=(
                pos_0.get_view(ilist.IList([0]), ilist.IList([0, 1, 2])),
                pos_1.get_view(ilist.IList([0]), ilist.IList([0, 1, 2])),
            )
        ),
        trajectory.Trajectory(
            waypoints=(
                pos_1.get_view(ilist.IList([0, 1]), ilist.IList([0, 1, 2])),
                pos_2.get_view(ilist.IList([0, 1]), ilist.IList([0, 1, 2])),
            )
        ),
        trajectory.Trajectory(
            waypoints=(
                pos_2.get_view(ilist.IList([0, 1]), ilist.IList([1, 2])),
                pos_3.get_view(ilist.IList([0, 1]), ilist.IList([1, 2])),
            )
        ),
    ]

    return (
        path.Path(
            x_tones=x_tones,
            y_tones=y_tones,
            path=actions,
        ),
        trajectories,
    )


def test_rewrite_play():
    pth = ir.TestValue()
    pth.type = path.PathType
    pth_value, trajectories = generate_path()
    pth.hints["const"] = const.Value(pth_value)

    test_region = ir.Region([ir.Block(), ir.Block([path.Play(pth)])])
    expected_region = ir.Region([ir.Block(), expected_block := ir.Block([])])

    curr_state = expected_block.args.append_from(
        trajectory.AtomStateType, name="atom_state"
    )

    for traj in trajectories:
        traj_stmt = py.Constant(traj)
        expected_block.stmts.append(traj_stmt)
        move_stmt = trajectory.Move(curr_state, traj_stmt.result)
        expected_block.stmts.append(move_stmt)
        curr_state = move_stmt.result

    rewrite.Walk(path2insight.PathToInsightRule()).rewrite(test_region)
    assert_nodes(test_region, expected_region)


def test_rewrite_play_skip():
    pth = ir.TestValue()

    test_region = ir.Region([ir.Block(), ir.Block([path.Play(pth)])])
    expected_region = ir.Region(
        [ir.Block(), expected_block := ir.Block([path.Play(pth)])]
    )
    expected_block.args.append_from(trajectory.AtomStateType, name="atom_state")

    rewrite.Walk(path2insight.PathToInsightRule()).rewrite(test_region)
    assert_nodes(test_region, expected_region)


def test_rewrite_branch():

    test_region = ir.Region(
        [ir.Block(), test_block := ir.Block(), exit_block := ir.Block()]
    )
    test_block.stmts.append(cf.Branch((), successor=exit_block))

    expected_region = ir.Region(
        [ir.Block(), expected_block := ir.Block(), exit_block := ir.Block()]
    )
    arg = expected_block.args.append_from(trajectory.AtomStateType, name="atom_state")
    expected_block.stmts.append(cf.Branch((arg,), successor=exit_block))
    exit_block.args.append_from(trajectory.AtomStateType, name="atom_state")

    rewrite.Walk(path2insight.PathToInsightRule()).rewrite(test_region)

    assert_nodes(test_region, expected_region)


def test_rewrite_conditional_branch():
    cond = ir.TestValue()
    test_region = ir.Region(
        [
            ir.Block(),
            test_block := ir.Block(),
            then_successor := ir.Block(),
            else_successor := ir.Block(),
        ]
    )
    test_block.stmts.append(
        cf.ConditionalBranch(
            cond, (), (), then_successor=then_successor, else_successor=else_successor
        )
    )

    expected_region = ir.Region(
        [
            ir.Block(),
            expected_block := ir.Block(),
            then_successor := ir.Block(),
            else_successor := ir.Block(),
        ]
    )
    arg = expected_block.args.append_from(trajectory.AtomStateType, name="atom_state")
    expected_block.stmts.append(
        cf.ConditionalBranch(
            cond,
            (arg,),
            (arg,),
            then_successor=then_successor,
            else_successor=else_successor,
        )
    )
    then_successor.args.append_from(trajectory.AtomStateType, name="atom_state")
    else_successor.args.append_from(trajectory.AtomStateType, name="atom_state")

    rewrite.Walk(path2insight.PathToInsightRule()).rewrite(test_region)

    assert_nodes(test_region, expected_region)


if __name__ == "__main__":
    test_rewrite_fill()
    test_rewrite_play()
    test_rewrite_play_skip()
    test_rewrite_branch()
    test_rewrite_conditional_branch()
    print("Test passed successfully.")

# %% [markdown]
# # Programming the move layout for logical magic state distillation

# %% [markdown]
# In this example, we program the move layout employed in the demonstration of logical
# magic state distillation for a distance-5 color code, as presented in QuEra’s recent
# publication: [**“Experimental demonstration of logical magic state distillation”,
# Nature, 2025**](https://arxiv.org/pdf/2506.14169).
# This example focuses specifically on the atom moves and two-qubit gate operations
# between atom pairs. For clarity, we omit the single-qubit gates used in the full
# circuit. The circuits executed in the paper were carefully optimized for the
# architectural features of QuEra’s neutral atom hardware. In particular, they leverage
# extensive parallelization of atom shuttling operations and simultaneous execution of
# two-qubit gates.
#
# We will demonstrate that `bloqade.shuttle` provides a concise and efficient interface
# for expressing such parallelized atom movements.
#
# As a first step, we import the relevant modules of `bloqade.shuttle` and `kirin`.

# %%
from typing import Any, TypeVar

import matplotlib
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import gate, init, spec
from bloqade.shuttle.prelude import move
from bloqade.shuttle.stdlib.spec import single_zone_spec
from bloqade.shuttle.stdlib.waypoints import move_by_waypoints
from bloqade.shuttle.visualizer import PathVisualizer

# %% [markdown]
# The primary subroutines used to implement atom transport are the `move` dialect and
# the `move_by_waypoints` function from the standard library. Programming atom movement
# in shuttle is centered around atoms arranged on two-dimensional grids. This reflects
# the capabilities of QuEra’s Gemini-class hardware, which utilizes pairs of
# acousto-optic deflectors (AODs) to manipulate atom positions independently in the
# x- and y-directions.
#
# Grid-based layouts are chosen to optimize both the accessibility and
# parallelizability of atom moves, given AOD constraints such as simultaneous pickup of
# atoms aligned along columns and rows, as well as the need to prevent inter-atomic
# collisions during transport. The shuttle framework encodes AOD constraints directly
# into the semantics of move kernel objects. Attempting to compile or execute a move
# sequence that violates these constraints will result in a runtime or compile-time
# error, ensuring physical feasibility of the programmed layout on hardware

# %% [markdown]
# As a first step, we define three global parameters that govern the geometry and
# dynamics of the atom array:
#
# - `grid_spacing`: Specifies the lattice spacing of the initial two-dimensional grid.
# This grid corresponds to the static trap array defined by the spatial light modulator
# (SLM), which generates the optical tweezers used to hold the atoms.
#
# - `entangling_pair_dist`: Sets the target distance between pairs of atoms that are
# intended to undergo a two-qubit entangling gate. This distance must be sufficiently
# small to enable a strong Rydberg-mediated interaction, which is essential for
# high-fidelity entanglement. A typical value used in experiments is 2 μm.
#
# - `path_shift_dist`: During atom transport, it is often necessary to temporarily
# displace atoms off-grid to avoid collisions when crossing rows or columns. This
# parameter defines the offset applied to atoms during their movement, enabling
# collision-free shuttling through the array.

# %%
# define global geometry choices
grid_spacing = 10.0  # spacing of the grid traps

entangling_pair_dist = 2.0  # distance between atom pairs getting entangled

path_shift_dist = (
    3.0  # distance that is used to shift the atom path out of the columns or rows
)

# %% [markdown]
# # Basic move pattern

# %% [markdown]
# In this section, we program the precise atom movement pattern used in the experimental
# demonstration of logical magic state distillation. Due to the high degree of
# connectivity required by the circuit, atom transport is restricted to full-row and
# full-column movements, maximizing parallelism while respecting hardware constraints.
#
# We begin by specifying the initial atom grid configuration. This example focuses on a
# single entangling zone layout, where each logical qubit is encoded along a single row
# of atoms. For a distance-5 color code, each logical qubit comprises 17 physical
# qubits. The experimental implementation involved five such logical qubits.
#
# This geometry is conveniently defined using the `single_zone_spec` function, where:
#
# - `num_x` specifies the number of columns (i.e., physical qubits per logical qubit),
# - `num_y` specifies the number of rows (i.e., logical qubits), and
# - `spacing` defines the uniform distance between adjacent rows and columns.
#
# By construction, the grid is assumed to be equidistant in both spatial dimensions.

# %%
arch_spec = single_zone_spec(num_x=17, num_y=5, spacing=grid_spacing)

# %% [markdown]
# We define a set of helper kernel functions to enable coordinated movement of atoms
# along rows and columns of the grid. The core routine, `entangle_cols`, operates on two
# `IList` arguments -- `ctrls` and `qargs`. The `ctrls` list specifies the row indices
# of control qubits to be moved, while `qargs` indicates the row indices of the target
# qubits with which entanglement is to be performed.
#
# To register the function as a valid movement kernel for compilation to
# `bloqade.shuttle` IR, we decorate it with `@move`. This ensures compatibility with
# `kirin`’s intermediate representation and hardware-aware compilation pipeline.
#
# The structure of the entangling routine comprises the following key steps:
#
# 1. Define initial trap sites: Specify the locations of static SLM-defined traps where
# all qubits are initially held.
#
# 2. Construct subgrids: Define subgrids corresponding to the atoms to be picked up
# (`ctrls`), and subgrids defining the positions of the target qubits (`qargs`) near
# which the control atoms will be temporarily positioned to enable interaction.
#
# 3. Specify waypoint trajectories: Construct ordered sequences of intermediate
# positions (waypoints) to guide atom transport between subgrids.
#
# 4. Invoke `move_by_waypoints`: Use this function to concatenate the defined path
# segments, producing the full motion trajectory between initial and final subgrid
# configurations.
#
# It is important to note that, in this layout, atoms always return to their original
# static trap positions following each entangling operation. This symmetry enables easy
# definition of the reverse path by simply inverting the sequence of waypoints.
#
# The `move_by_waypoints` function includes Boolean flags that indicate whether atoms
# should be picked up from or dropped into static traps at each stage. In the context
# of this circuit, we maintain atoms within the AODs during gate execution and only
# return them to their SLM-defined traps afterward. This is a deliberate design choice
# and not a general constraint. More sophisticated pickup/dropoff sequences can be
# constructed using multiple defined trap grids. However, care must be taken: dropping
# an atom at a site lacking an active trap will result in atom loss.


# %%
@move
def entangle_cols(ctrls: ilist.IList[int, Any], qargs: ilist.IList[int, Any]):
    """Function to entangle columns of atoms."""

    # fill the defined zone specification with traps
    zone = spec.get_static_trap(zone_id="traps")
    # get the shape of the trap array
    traps_shape = grid.shape(zone)
    # generate an ilist from 0 to the number of rows in the trap array
    all_rows = ilist.range(traps_shape[1])

    # subgrid of control qubits that are picked up
    src = grid.sub_grid(zone, ctrls, all_rows)
    # subgrid of target qubits that are entangled with the control qubits
    dst = grid.sub_grid(zone, qargs, all_rows)

    # define the moves
    # shifting the src grid down along the y-axis
    first_waypoint = grid.shift(src, 0.0, -path_shift_dist)

    # shift the to the respective x-positions of the target
    # qubits and add an offset in the x-direction
    second_waypoint = grid.shift(dst, -entangling_pair_dist, -path_shift_dist)

    # shift the dst grid back up into the original y-position
    # to form atom pairs that will get a gate
    third_waypoint = grid.shift(dst, -entangling_pair_dist, 0.0)

    # combine the waypoints into an ilist
    waypoints = ilist.IList([src, first_waypoint, second_waypoint, third_waypoint])
    # the revese waypoints defining the reverse path back to the original positions
    reverse_waypoints = ilist.IList(
        [third_waypoint, second_waypoint, first_waypoint, src]
    )

    # move the qubits along the waypoints, True means that the atoms are picked up
    # and False means that they are not dropped at the end of the move
    move_by_waypoints(waypoints, True, False)
    # apply the entangling gate to the atoms that are now in the right positions
    # (paired up)
    gate.top_hat_cz(zone)
    # move the atoms back to their original positions, False means that the atoms
    # are not picked up (since they are still in the AOD) and True means that they
    # are dropped back into their static trap site at the end of the move
    move_by_waypoints(reverse_waypoints, False, True)


# %% [markdown]
# In an analogous manner, we can now define parallel transport operations for atoms
# along rows of the grid.


# %%
@move
def entangle_rows(ctrls: ilist.IList[int, Any], qargs: ilist.IList[int, Any]):
    """Function to entangle rows of atoms."""

    # get the positions of the static traps in the entangling zone
    zone = spec.get_static_trap(zone_id="traps")
    # get the shape of the trap array
    traps_shape = grid.shape(zone)
    # generate an ilist from 0 to the number of columns in the trap array
    all_cols = ilist.range(traps_shape[0])

    src = grid.sub_grid(zone, all_cols, ctrls)
    dst = grid.sub_grid(zone, all_cols, qargs)

    # define the moves
    # shift the src grid to the right along the x-axis
    first_waypoint = grid.shift(src, entangling_pair_dist, 0.0)
    # move the src grid to the y-positions of the target qubits
    second_waypoint = grid.shift(dst, entangling_pair_dist, 0.0)

    # combine the waypoints into an ilist
    waypoints = ilist.IList([src, first_waypoint, second_waypoint])
    # the revese waypoints defining the reverse path back to the original positions
    reverse_waypoints = ilist.IList([second_waypoint, first_waypoint, src])

    # move the qubits along the waypoints, True means that the atoms are picked up
    # and False means that they are not dropped at the end of the move
    move_by_waypoints(waypoints, True, False)
    # apply the entangling gate to the atoms that are now in the right positions
    # (paired up)
    gate.top_hat_cz(zone)
    # move the atoms back to their original positions, False means that the atoms
    # are not picked up (since they are still in the AOD) and True means that they
    # are dropped back into their static trap site at the end of the move
    move_by_waypoints(reverse_waypoints, False, True)


# %% [markdown]
# Using these helper functions, we can now specify the complete move pattern in just a
# few lines of code by providing the control and target atom indices to the
# `entangle_cols` and `entangle_rows` functions.
#
# As before, we define this as a kernel function, annotated with the `@move` decorator
# to indicate compatibility with the bloqade.shuttle IR. This kernel is wrapped inside
# a closure and returned as a first-class move kernel function.


# %%
def make_main(entangle_cols, entangle_rows):
    """Helper function to create the main move kernel for logical magic state
    distillation.

    Args
        entangle_cols: Function to entangle columns of atoms.
        entangle_rows: Function to entangle rows of atoms.

    Returns
        main: The main move kernel function that defines the entire move pattern.

    """

    @move
    def main():
        """Main move kernel function that defines the entire move pattern for the
        logical magic state distillation experiment.

        """

        init.fill([spec.get_static_trap(zone_id="traps")])

        # encode logical qubits by entangling pairs of atoms in columns
        entangle_cols([1, 10, 12, 13], [3, 7, 14, 16])
        entangle_cols([4, 8, 11, 15], [7, 10, 14, 16])
        entangle_cols([2, 8, 9, 10, 14], [4, 6, 7, 13, 16])
        entangle_cols([0, 3, 5, 10, 11], [2, 6, 8, 12, 13])
        entangle_cols([0, 2, 4, 6, 8, 12], [1, 3, 5, 7, 9, 15])

        # logical qubit operations by moving entire rows of atoms
        entangle_rows([0, 2], [1, 3])
        entangle_rows([1, 3], [2, 4])
        entangle_rows([3, 4], [0, 1])

    return main


ker = make_main(entangle_cols, entangle_rows)

# %% [markdown]
# We can verify the correctness of the programmed move layout using the `PathVisualizer`
# utility provided by `bloqade.shuttle`. This tool displays the atom trajectories
# between defined waypoints and enables stepwise inspection of the full movement
# sequence via the `Continue` button. Red flashes are used to indicate the application
# of two-qubit gate pulses at the entangling zone during the sequence.

# %%
matplotlib.use("TkAgg")  # requirement for PathVisualizer

PathVisualizer(ker.dialects, arch_spec=arch_spec).run(ker, ())

# %% [markdown]
# # Further refining the move pattern

# %% [markdown]
# We now take a further step by introducing a slight optimization to the move pattern.
# In the previous example, control qubits were moved in both leftward and rightward
# directions, but ultimately all were positioned to the left of their respective target
# qubits. This introduces unnecessary displacement for half of the control atoms. To
# minimize total movement, we can instead position control atoms to the nearest side of
# the target qubits, i.e., those moving rightward are placed to the left, and those
# moving leftward are placed to the right of the targets.
#
# To implement this, we define an additional helper function that computes the nearest
# feasible final position for each control qubit, given the target layout and movement
# direction.

# %%
N = TypeVar("N")


@move
def get_final_positions(
    src: ilist.IList[float, N], dst: ilist.IList[float, N], offset: float
):
    """Helper function to compute the nearest final positions for entanglement."""

    assert len(src) == len(
        dst
    ), "Source and destination lists must be of the same length."

    def get_last_pos(i: int) -> float:
        assert src[i] != dst[i], "Source and destination positions must not be equal."
        if src[i] < dst[i]:
            return dst[i] - offset
        elif src[i] > dst[i]:
            return dst[i] + offset
        else:
            return dst[i]

    return ilist.map(get_last_pos, ilist.range(len(src)))


# %% [markdown]
# Using this helper function, we can now construct new waypoint sequences that
# incorporate the nearest final positions for the control qubits.


# %%
@move
def entangle_cols_low_dist(ctrls: ilist.IList[int, Any], qargs: ilist.IList[int, Any]):
    """Helper function to entangle columns of atoms on a grid in a single entangling
    zone with optimized final positions (nearest location).

    """

    zone = spec.get_static_trap(zone_id="traps")
    traps_shape = grid.shape(zone)
    all_rows = ilist.range(traps_shape[1])

    src = grid.sub_grid(zone, ctrls, all_rows)
    dst = grid.sub_grid(zone, qargs, all_rows)

    first_waypoint = grid.shift(src, 0.0, -path_shift_dist)

    dst_x = grid.get_xpos(dst)
    src_x = grid.get_xpos(src)

    last_x = get_final_positions(
        src_x, dst_x, entangling_pair_dist
    )  # get the nearest final positions for the control qubits

    second_pos = grid.from_positions(last_x, grid.get_ypos(first_waypoint))
    last_pos = grid.from_positions(last_x, grid.get_ypos(dst))

    waypoints = ilist.IList([src, first_waypoint, second_pos, last_pos])
    reverse_waypoints = ilist.IList([last_pos, second_pos, first_waypoint, src])

    move_by_waypoints(waypoints, True, False)
    gate.top_hat_cz(zone)
    move_by_waypoints(reverse_waypoints, False, True)


# %% [markdown]
# We can now define a new move kernel that implements the optimized column-wise
# transport pattern using the updated waypoint assignments.

# %%
ker = make_main(entangle_cols_low_dist, entangle_rows)

# %% [markdown]
# Finally, we can once again visualize the optimized move pattern using the
# PathVisualizer to inspect the resulting trajectories and validate the
# updated layout.

# %%
matplotlib.use("TkAgg")  # requirement for PathVisualizer

PathVisualizer(ker.dialects, arch_spec=arch_spec).run(ker, ())

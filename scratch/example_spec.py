from typing import Any
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

# UCLA architecture spec

# Approach 1:
#   Each zone is described by a grid. Each slm array in the spec is a subgrid.
#   Assume traps of an entanglement site are placed either horizontally or vertically
#       Comments: UCLA spec is more expressive. Traps are can be placed diagonally.

# Approach 2:
#   Each slm is described by a grid. A zone consists of multiple grid. However, it is
#   non-trivial to perfrom Rydberg gates (not on a single grid)

# Approach 3:
#   Each zone is described by a grid. Each slm array in the spec is a subgrid. To support
#   may construct arbitrary shape, we construct additional sites that will not be used

# Implementation follows approach 1


# example architecture for scratch/hardware_example/qcrank_architecture_4_2_v.json
# 1 entanglement zone, no storage zone
def qcrank_architecture_4_2_v():
    # traps are placed vertically
    # information is derived from the arch spec. Assume those info are consistent across
    # all SLMs of the same zone.
    x_offset, y_offset = 0, 5
    trap_spacing = 2
    x_spacing, y_spacing = 10, 12
    r, c = 2, 8
    x_positions = [x_offset + x_spacing * i for i in range(c)]
    y_positions = sorted([
        y_offset + shift + y_spacing * i
        for shift in (0, trap_spacing)
        for i in range(r)
    ])
    traps: grid.Grid[Any, Any] = grid.Grid.from_positions(
        x_positions=x_positions, y_positions=y_positions
    )

    all_x: ilist.IList[int, Any] = ilist.IList(data=range(traps.shape[0]))
    lower_col_idx: ilist.IList[int, Any] = ilist.IList(data=range(0, traps.shape[1], 2))
    upper_col_idx: ilist.IList[int, Any] = ilist.IList(data=range(1, traps.shape[1], 2))

    lower_traps = traps.get_view(x_indices=all_x, y_indices=lower_col_idx)
    upper_traps = traps.get_view(x_indices=all_x, y_indices=upper_col_idx)

    static_traps: dict[str, grid.Grid[Any, Any]] = {
        "traps": traps,
        "lower_traps": lower_traps,
        "upper_traps": upper_traps,
    }

    return static_traps


def generate_entanglement_zone_horizontal_traps(
    offset: tuple[int, int],
    trap_spacing: int,
    site_spacing: tuple[int, int],
    num_row: int,
    num_column: int,
) -> grid.Grid[Any, Any]:
    pass
    x_offset, y_offset = offset
    x_spacing, y_spacing = site_spacing
    x_positions_entanglement = sorted([
        x_offset + shift + x_spacing * i
        for shift in (0, trap_spacing)
        for i in range(num_column)
    ])
    y_positions_entanglement = [y_offset + y_spacing * i for i in range(num_row)]

    traps: grid.Grid[Any, Any] = grid.Grid.from_positions(
        x_positions=x_positions_entanglement, y_positions=y_positions_entanglement
    )
    return traps


# example architecture for scratch/hardware_example/small_architecture.json
# 1 entanglement zone, 1 storage zone
def small_architecture():
    # traps are placed horizontally
    # entanglement zone
    offset_entanglement = (3, 16)
    site_spacing = (12, 10)
    num_row, num_column = 6, 10

    traps_entanglement = generate_entanglement_zone_horizontal_traps(
        offset=offset_entanglement,
        trap_spacing=2,
        site_spacing=site_spacing,
        num_row=num_row,
        num_column=num_column,
    )

    left_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(0, traps_entanglement.shape[0], 2)
    )
    right_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(1, traps_entanglement.shape[0], 2)
    )
    all_y: ilist.IList[int, Any] = ilist.IList(data=range(traps_entanglement.shape[1]))

    left_traps = traps_entanglement.get_view(x_indices=left_col_idx, y_indices=all_y)
    right_traps = traps_entanglement.get_view(x_indices=right_col_idx, y_indices=all_y)

    # storage zone
    x_offset_storage, y_offset_storage = 0, 0
    x_spacing_storage, y_spacing_storage = 3, 3
    r_storage, c_storage = 3, 40

    x_positions_storage = [
        x_offset_storage + x_spacing_storage * i for i in range(c_storage)
    ]
    y_positions_storage = [
        y_offset_storage + y_spacing_storage * i for i in range(r_storage)
    ]

    traps_storage: grid.Grid[Any, Any] = grid.Grid.from_positions(
        x_positions=x_positions_storage, y_positions=y_positions_storage
    )

    static_traps: dict[str, grid.Grid[Any, Any]] = {
        "traps_entanglement": traps_entanglement,
        "left_traps_entanglement": left_traps,
        "right_traps_entanglement": right_traps,
        "traps_storage": traps_storage,
    }

    return static_traps


# example architecture for scratch/hardware_example/small_architecture_2Ryd.json
# 1 entanglement zone, 1 storage zone
def small_architecture_2Ryd():
    # traps are placed horizontally
    # entanglement zone 0
    offset_entanglement = (3, 16)
    site_spacing = (12, 10)
    num_row, num_column = 6, 10

    traps_entanglement_0 = generate_entanglement_zone_horizontal_traps(
        offset=offset_entanglement,
        trap_spacing=2,
        site_spacing=site_spacing,
        num_row=num_row,
        num_column=num_column,
    )

    left_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(0, traps_entanglement_0.shape[0], 2)
    )
    right_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(1, traps_entanglement_0.shape[0], 2)
    )
    all_y: ilist.IList[int, Any] = ilist.IList(
        data=range(traps_entanglement_0.shape[1])
    )

    left_traps_0 = traps_entanglement_0.get_view(
        x_indices=left_col_idx, y_indices=all_y
    )
    right_traps_0 = traps_entanglement_0.get_view(
        x_indices=right_col_idx, y_indices=all_y
    )

    # entanglement zone 1
    offset_entanglement = (3, -30)
    site_spacing = (12, 10)
    num_row, num_column = 6, 10

    traps_entanglement_1 = generate_entanglement_zone_horizontal_traps(
        offset=offset_entanglement,
        trap_spacing=2,
        site_spacing=site_spacing,
        num_row=num_row,
        num_column=num_column,
    )

    left_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(0, traps_entanglement_1.shape[0], 2)
    )
    right_col_idx: ilist.IList[int, Any] = ilist.IList(
        data=range(1, traps_entanglement_1.shape[0], 2)
    )
    all_y: ilist.IList[int, Any] = ilist.IList(
        data=range(traps_entanglement_1.shape[1])
    )

    left_traps_1 = traps_entanglement_1.get_view(
        x_indices=left_col_idx, y_indices=all_y
    )
    right_traps_1 = traps_entanglement_1.get_view(
        x_indices=right_col_idx, y_indices=all_y
    )

    # storage zone
    x_offset_storage, y_offset_storage = 0, 0
    x_spacing_storage, y_spacing_storage = 3, 3
    r_storage, c_storage = 3, 40

    x_positions_storage = [
        x_offset_storage + x_spacing_storage * i for i in range(c_storage)
    ]
    y_positions_storage = [
        y_offset_storage + y_spacing_storage * i for i in range(r_storage)
    ]

    traps_storage: grid.Grid[Any, Any] = grid.Grid.from_positions(
        x_positions=x_positions_storage, y_positions=y_positions_storage
    )

    static_traps: dict[str, grid.Grid[Any, Any]] = {
        "traps_entanglement_0": traps_entanglement_0,
        "left_traps_entanglement_0": left_traps_0,
        "right_traps_entanglement_0": right_traps_0,
        "traps_entanglement_1": traps_entanglement_1,
        "left_traps_entanglement_1": left_traps_1,
        "right_traps_entanglement_1": right_traps_1,
        "traps_storage": traps_storage,
    }

    return static_traps
print("Monolithic architecture: 8 col, 2 row, vertical traps")
arch = qcrank_architecture_4_2_v()
for key in arch:
    print(key)
    print(arch[key])

print("\nZoned architecture with one 6*10 entanglement zone and one 3*40 storage zone, horizontal traps")
arch = small_architecture()
for key in arch:
    print(key)
    print(arch[key])

print("\nZoned architecture with two 6*10 entanglement zones and one 3*40 storage zone, horizontal traps")
arch = small_architecture_2Ryd()
for key in arch:
    print(key)
    print(arch[key])

from bloqade.geometry.dialects import grid

from bloqade.shuttle.arch import ArchSpec, Layout


def get_base_spec():
    ROW_SEPARATION = 10.0
    COL_SEPARATION = 8.0
    STORAGE_ALLY_WIDTH = 6.0
    GATE_SPACING = 2.0

    num_x = 17
    num_y = 5
    column_spacing = COL_SEPARATION
    row_spacing = ROW_SEPARATION
    gate_spacing = GATE_SPACING  # space between atoms for CZ gate.

    single_gate = grid.Grid.from_positions((0.0, gate_spacing), (0.0,))
    all_entangling_zone_traps = single_gate.repeat(
        num_x, num_y, column_spacing, row_spacing
    ).shift(-81.0, -20.0)

    reservoir_ally_width = STORAGE_ALLY_WIDTH
    reservoir_column_spacing = column_spacing + gate_spacing - reservoir_ally_width
    reservoir_row_spacing = 4.0
    num_reservoir_rows = 19

    reservoir_pair = grid.Grid.from_positions((0.0, reservoir_ally_width), (0.0,))

    reservoir = reservoir_pair.repeat(
        num_x, num_reservoir_rows, reservoir_column_spacing, reservoir_row_spacing
    )

    top_reservoir = reservoir.shift(-81.0 - reservoir_ally_width, row_spacing * 3)
    bottom_reservoir = reservoir.shift(
        -81.0 - reservoir_ally_width,
        -3.0 * row_spacing - reservoir_row_spacing * (num_reservoir_rows - 1),
    )

    # various slices of the zones for convenience

    aom_sites = all_entangling_zone_traps[::2, :].shift(-GATE_SPACING, 0)

    static_traps = {
        "gate_zone": all_entangling_zone_traps,
        "top_reservoir": top_reservoir,
        "bottom_reservoir": bottom_reservoir,
    }

    layout = Layout(
        static_traps,
        set(),
        set(),
        set(),
        special_grid={
            "aom_sites": aom_sites,
        },
    )
    return ArchSpec(
        layout,
        float_constants={
            "row_separation": ROW_SEPARATION,
            "col_separation": COL_SEPARATION,
            "gate_spacing": GATE_SPACING,
        },
    )

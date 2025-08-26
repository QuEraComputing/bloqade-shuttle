import json
from typing import Any, Literal, TypeVar

import numpy as np
from bloqade.geometry.dialects import grid
from kirin.dialects import ilist
from lower_zair import ShuttleBuilder

from bloqade.shuttle import action, gate, init, measure, schedule, spec
from bloqade.shuttle.prelude import move, tweezer
from bloqade.shuttle.stdlib.layouts.two_col_zone import rearrange
from bloqade.shuttle.visualizer import MatplotlibRenderer, PathVisualizer


def run_qcrank(filename: str):
    with open(filename, "r") as f:
        compiled_qcrank = json.load(f)

    arch_filename = compiled_qcrank["architecture_spec_path"]

    with open(arch_filename, "r") as f:
        architecture_spec = json.load(f)

    # set architecture
    # assume single entagnlement zone
    entanglement_zone_spec = architecture_spec["entanglement_zones"][0]
    slms = entanglement_zone_spec["slms"]
    assert len(slms) == 2
    slm1 = slms[0]
    slm2 = slms[1]
    assert slm1["r"] == slm2["r"]
    assert slm1["c"] == slm2["c"]
    assert slm1["site_seperation"] == slm2["site_seperation"]
    assert slm1["location"][0] == slm2["location"][0]
    dis_trap = abs(slm1["location"][1] - slm2["location"][1])
    dis_site = slm1["site_seperation"][1] - dis_trap
    x_spacing = [slm1["site_seperation"][0] * (slm1["c"] - 1)]
    y_spacing = []
    for _ in range(slm1["r"]):
        y_spacing.append(dis_trap)
        y_spacing.append(dis_site)

    slm0 = grid.Grid(
        x_spacing=tuple(x_spacing),
        y_spacing=tuple(y_spacing),
        x_init=slm1["location"][0],
        y_init=slm1["location"][1],
    )

    x_spacing = [slm1["site_seperation"][0]] * (slm1["c"] - 1)
    y_spacing = [slm1["site_seperation"][1]] * (slm1["r"] - 1)
    slm1 = grid.Grid(
        x_spacing=tuple(x_spacing),
        y_spacing=tuple(y_spacing),
        x_init=slm1["location"][0],
        y_init=slm1["location"][1],
    )
    x_spacing = [slm2["site_seperation"][0]] * (slm2["c"] - 1)
    y_spacing = [slm2["site_seperation"][1]] * (slm2["r"] - 1)
    slm2 = grid.Grid(
        x_spacing=tuple(x_spacing),
        y_spacing=tuple(y_spacing),
        x_init=slm2["location"][0],
        y_init=slm2["location"][1],
    )
    spec_value = spec.ArchSpec(
        layout=spec.Layout(
            static_traps={
                "slm0": slm0,
                "slm1": slm1,
                "slm2": slm2,
            },
            fillable=set(["slm1", "slm2"]),
        )
    )
    # print(spec_value)

    spec_mapping = {0: "slms", 1: "slm1", 2: "slm2"}
    num_qubits = len(compiled_qcrank["instructions"][0]["init_locs"])
    shuttle_builder = ShuttleBuilder(
        spec_mapping=spec_mapping,
        move_kernel=rearrange,
        num_qubits=num_qubits
    )
    method = shuttle_builder.lower(compiled_qcrank)
    # print(method.print())


if __name__ == "__main__":
    filename = "scratch/qcr_4a8d_quera_circ_code.json"
    run_qcrank(filename)

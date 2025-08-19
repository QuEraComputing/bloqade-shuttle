from typing import Any, Literal, TypeVar

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist

from bloqade.shuttle import action, gate, init, measure, schedule, spec
from bloqade.shuttle.prelude import move, tweezer
from bloqade.shuttle.visualizer import MatplotlibRenderer, PathVisualizer
from lower_zair import ShuttleBuilder
import json
import numpy as np

def run_qcrank(filename: str):
    with open(filename, 'r') as f:
        compiled_qcrank = json.load(f)
    
    arch_filename = compiled_qcrank["architecture_spec_path"]

    with open(arch_filename, 'r') as f:
        architecture_spec = json.load(f)

    # set architecture
    # assume single entagnlement zone
    entanglement_zone_spec =  architecture_spec["entanglement_zones"][0]
    slms = entanglement_zone_spec["slms"]
    assert len(slms) == 2
    slm0 = slms[0]
    slm1 = slms[1]
    assert slm0["r"] == slm1["r"]
    assert slm0["c"] == slm1["c"]
    assert slm0["site_seperation"] == slm1["site_seperation"]
    put_vertical = True
    if slm0["location"][1] == slm1["location"][1]:
        put_vertical = False
    if put_vertical:
        dis_trap = abs(slm0["location"][1] - slm1["location"][1])
        dis_site = slm0["site_seperation"][1] - dis_trap
        x_spacing = [slm0["site_seperation"][0] * (slm0["r"] - 1)]
        y_spacing = []
        for _ in range(slm0["c"]):
            y_spacing.append(dis_trap)
            y_spacing.append(dis_site)
    else:
        dis_trap = abs(slm0["location"][0] - slm1["location"][0])
        dis_site = slm0["site_seperation"][0] - dis_trap
        y_spacing = [slm0["site_seperation"][1] * (slm0["r"] - 1)]
        x_spacing = []
        for _ in range(slm0["c"]):
            x_spacing.append(dis_trap)
            x_spacing.append(dis_site)
        x_spacing = x_spacing
    
    inst_init = compiled_qcrank["instructions"][0]
    init_quibt_location = inst_init["init_locs"]
    
    shuttle_builder = ShuttleBuilder(num_qubits = len(init_quibt_location))
    shuttle_builder.construct_grid(entanglement_zone_spec['zone_id'],
                                   entanglement_zone_spec["offset"],
                                   x_spacing,
                                   y_spacing,
                                   entanglement_zone_spec["dimension"])

    spec_value = spec.ArchSpec(
        layout=spec.Layout(
            static_traps={
                "mem": shuttle_builder.grid_mapping,
            },
            fillable=set(["mem"]),
        )
    )

    grid_init_quibt_location = []
    for loc in init_quibt_location:
        x = loc[2]
        y = loc[3]
        if put_vertical:
            y *= 2
        else:
            x *= 2
        grid_init_quibt_location.append((x,y))
    
    def main():
        # init.fill([spec.get_static_trap(zone_id="mem")])
        init.fill(shuttle_builder.grid_mapping) # !
        insts = compiled_qcrank["instructions"][1:]
        for inst in insts:
            if inst["type"] == "1qGate":
                if inst["unitary"] == "ry":
                    for loc in inst["locs"]:
                        rotation_angle = np.random.random()
                        if loc[1] == 1:
                            locs = [(loc[0], 2 * loc[2], loc[3])]
                        else:
                            locs = [(loc[0], loc[2], loc[3])]
                        shuttle_builder.r_gate(0, rotation_angle, locs)
                elif inst["unitary"] == "h":
                    shuttle_builder.lower_h(inst["locs"])

            elif inst["type"] == "rydberg":
                shuttle_builder.entangle(inst["zone_id"])
            elif inst["type"] == "rearrangeJob":
                shuttle_builder.insert_move(inst["begin_locs"], inst["end_locs"])
        return measure.measure((shuttle_builder.grid_mapping,))

    return main, spec_value


def run_plotter(filename: str):
    main, spec_value = run_qcrank(filename)
    renderer = MatplotlibRenderer()
    PathVisualizer(main.dialects, renderer=renderer, arch_spec=spec_value).run(main, ())


if __name__ == "__main__":
    filename = "scratch/qcr_4a8d_quera_circ_code.json"
    run_plotter(filename)
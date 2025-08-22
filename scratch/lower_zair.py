import json
import math
from dataclasses import dataclass, field
from typing import Any, Generic, Sequence, TypeVar

from kirin import ir, types
from kirin.dialects import func, ilist, py
from kirin.dialects.ilist import IList

from bloqade.shuttle.dialects import filled, gate, init, spec
from bloqade.shuttle.prelude import move


def _simple_region() -> ir.Region:
    return ir.Region(ir.Block())


@dataclass
class ShuttleBuilder:

    spec_mapping: dict[int, str]
    move_kernel: ir.Method[
        [IList[int, Any], IList[int, Any], IList[int, Any], IList[int, Any]], None
    ]
    num_qubits: int

    body: ir.Region = field(default_factory=_simple_region, init=False)

    def push_stmt(self, stmt: ir.Statement):
        self.body.blocks[0].stmts.append(stmt)
        return stmt

    def push_constant(self, value: Any) -> ir.SSAValue:
        const_stmt = py.Constant(value)
        return self.push_stmt(const_stmt).expect_one_result()

    def get_zone(self, zone_id: int) -> ir.SSAValue:
        return self.push_stmt(
            spec.GetStaticTrap(zone_id=self.spec_mapping[zone_id])
        ).expect_one_result()

    def get_slm(
        self,
        slm_id: int,
    ):
        return self.push_stmt(
            spec.GetStaticTrap(zone_id=self.spec_mapping[slm_id])
        ).expect_one_result()

    def lower_rearrange(
        self,
        begin_locs: Sequence[tuple[int, int, int, int]],
        end_locs: Sequence[tuple[int, int, int, int]],
    ):
        # ignoring zone mapping, only include all unique x and y positions
        x_src = IList(sorted(set(src[2] for src in begin_locs)))
        y_src = IList(sorted(set(src[3] for src in begin_locs)))
        x_dst = IList(sorted(set(dst[2] for dst in end_locs)))
        y_dst = IList(sorted(set(dst[3] for dst in end_locs)))

        x_src_ref = self.push_constant(x_src)
        y_src_ref = self.push_constant(y_src)
        x_dst_ref = self.push_constant(x_dst)
        y_dst_ref = self.push_constant(y_dst)

        self.push_stmt(
            func.Invoke(
                inputs=(x_src_ref, y_src_ref, x_dst_ref, y_dst_ref),
                callee=self.move_kernel,
                kwargs=(),
            )
        )

    def rydberg(self, zone_id: int):
        self.push_stmt(gate.TopHatCZ(self.get_zone(zone_id)))

    def lower_ry_gate(
        self,
        rotation_angle: float,
        locs: Sequence[tuple[int, int, int, int]],
    ):
        filled_locs: dict[int, list[tuple[int, int]]] = {}

        for _, grid_id, x, y in locs:
            filled_locs.setdefault(grid_id, []).append((x, y))

        filled_loc_refs: list[ir.SSAValue] = []

        for grid_id, coords in filled_locs.items():
            locs_ref = self.push_constant(ilist.IList(coords))
            filled_loc_refs.append(
                self.push_stmt(
                    filled.Fill(self.get_slm(grid_id), locs_ref)
                ).expect_one_result()
            )

        axis_angle = self.push_constant(0.5)
        rotation_angle_ref = self.push_constant(rotation_angle / (2 * math.pi))

        for filled_ref in filled_loc_refs:
            self.push_stmt(gate.LocalR(axis_angle, rotation_angle_ref, filled_ref))

    def lower_rz_gate(
        self, rotation_angle: float, locations: Sequence[tuple[int, int, int, int]]
    ):
        filled_locs: dict[int, list[tuple[int, int]]] = {}

        for _, grid_id, x, y in locations:
            filled_locs.setdefault(grid_id, []).append((x, y))

        filled_loc_refs: list[ir.SSAValue] = []

        for grid_id, coords in filled_locs.items():
            locs_ref = self.push_constant(ilist.IList(coords))
            filled_loc_refs.append(
                self.push_stmt(
                    filled.Fill(self.get_slm(grid_id), locs_ref)
                ).expect_one_result()
            )

        rotation_angle_ref = self.push_constant(rotation_angle / (2 * math.pi))

        for filled_ref in filled_loc_refs:
            self.push_stmt(gate.LocalRz(rotation_angle_ref, filled_ref))

    def lower_h(self, locs: Sequence[tuple[int, int, int, int]]):
        quarter_rotation = self.push_constant(0.25)
        zero = self.push_constant(0.0)
        half_rotation = self.push_constant(0.5)
        if len(locs) == self.num_qubits:

            self.push_stmt(gate.GlobalRz(quarter_rotation))
            self.push_stmt(gate.GlobalR(zero, half_rotation))
            self.push_stmt(gate.GlobalRz(quarter_rotation))

    def lower_init(self, locs: Sequence[tuple[int, int, int, int]]):
        filled_locs: dict[int, list[tuple[int, int]]] = {}

        for _, grid_id, x, y in locs:
            filled_locs.setdefault(grid_id, []).append((x, y))

        filled_loc_refs: list[ir.SSAValue] = []

        for grid_id, coords in filled_locs.items():
            locs_ref = self.push_constant(ilist.IList(coords))
            filled_loc_refs.append(
                self.push_stmt(
                    filled.Fill(self.get_slm(grid_id), locs_ref)
                ).expect_one_result()
            )

        locations = self.push_constant(ilist.IList(filled_loc_refs))
        self.push_stmt(init.Fill(locations))

    def lower_instruction(self, instruction: dict[str, Any]):
        match instruction:
            case {"type": "init", "locs": locs}:
                self.lower_init(locs)
            case {"type": "1qGate", "unitary": "ry", "locs": locs, "angle": angle}:
                self.lower_ry_gate(angle, locs)
            case {"type": "1qGate", "unitary": "h", "locs": locs}:
                self.lower_h(locs)
            case {"type": "rydberg", "zone_id": zone_id}:
                self.rydberg(zone_id)
            case {
                "type": "rearrangeJob",
                "begin_locs": begin_locs,
                "end_locs": end_locs,
            }:
                self.lower_rearrange(begin_locs, end_locs)

    def lower(self, program: dict[str, Any]) -> ir.Method:
        """Entry point for lowering a ZAIR program

        Args:
            program (dict[str, Any]): JSON representation of the ZAIR program

        Returns:
            ir.Method: Lowered IR method
        """
        sym_name = program["name"]
        signature = func.Signature((), types.NoneType)

        for inst in program["instructions"]:
            self.lower_instruction(inst)

        code = func.Function(
            sym_name=sym_name,
            signature=signature,
            body=self.body,
        )
        return ir.Method(None, None, sym_name, [], move, code)

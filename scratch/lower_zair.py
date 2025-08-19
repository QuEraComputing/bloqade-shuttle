from dataclasses import dataclass, field
import math
from typing import Any, Sequence
from kirin import ir
from kirin.dialects.ilist import IList
from kirin.dialects import py, func, ilist
from bloqade.geometry import grid
from bloqade.shuttle.dialects import gate, filled

def _simple_region() -> ir.Region:
    return ir.Region(ir.Block())


@dataclass
class ShuttleBuilder:
    move_kernel: ir.Method[[IList[tuple[int, int]], IList[tuple[int, int]]], None]
    num_qubits: int

    body: ir.Region = field(default_factory=_simple_region, init=False)
    grid_mapping: ir.SSAValue = None

    def push_stmt(self, stmt: ir.Statement):
        self.body.blocks[0].stmts.append(stmt)
        return stmt

    def push_constant(self, value: Any) -> ir.SSAValue:
        const_stmt = py.Constant(value)
        return self.push_stmt(const_stmt).expect_one_result()

    def construct_grid(
        self,
        grid_id: int,
        offset: tuple[int, int],
        x_spacing: list[int],
        y_spacing: list[int],
        dim: tuple[int, int],
    ):
        x_init = offset[0]
        y_init = offset[1]

        grid_ref = self.push_constant(
            grid.Grid(
                x_spacing=tuple(x_spacing), y_spacing=tuple(y_spacing), x_init=x_init, y_init=y_init
            )
        )

        self.grid_mapping = grid_ref

        return grid_ref

    def insert_move(
        self,
        srcs: Sequence[tuple[int, int, int, int]],
        dsts: Sequence[tuple[int, int, int, int]],
    ):
        # ignoring zone mapping,
        sorted_srcs = sorted(srcs, key=lambda x: x[0])
        sorted_dsts = sorted(dsts, key=lambda x: x[0])

        x_src = IList([src[2] for src in sorted_srcs])
        y_src = IList([src[3] for src in sorted_srcs])
        # assume only address qubits will move
        x_dst = IList([dst[2] * 2 for dst in sorted_dsts])
        y_dst = IList([dst[3] * 2 for dst in sorted_dsts])

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
        
    def entangle(self, grid_id: int):
        self.push_stmt(gate.TopHatCZ(self.grid_mapping[grid_id]))

    def r_gate(
        self,
        axis_angle: float,
        rotation_angle: float,
        locs: Sequence[tuple[int, int, int]],
    ):
        filled_locs = {}

        for _, x, y in locs:
            filled_locs.setdefault(0, []).append((x, y))

        filled_loc_refs: dict[int, ir.SSAValue] = {}

        for grid_id, locs in filled_locs.items():
            locs_ref = self.push_constant(locs)
            filled_loc_refs[grid_id] = self.push_stmt(
                filled.Fill(self.grid_mapping[grid_id], locs_ref)
            ).expect_one_result()

        axis_angle_ref = self.push_constant(axis_angle / (2 * math.pi))
        rotation_angle_ref = self.push_constant(rotation_angle / (2 * math.pi))

        for filled_ref in filled_loc_refs.values():
            self.push_stmt(gate.LocalR(axis_angle_ref, rotation_angle_ref, filled_ref))

    def lower_h(self, locs: Sequence[tuple[int, int, int, int]]):
        assert len(locs) == self.num_qubits, "H gate must be applied to all qubits"
        self.push_stmt(gate.GlobalRz(0.25))
        self.push_stmt(gate.GlobalR(0, 0.5))
        self.push_stmt(gate.GlobalRz(0.25))

        

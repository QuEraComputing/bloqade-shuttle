from dataclasses import dataclass, field
import math
from typing import Any, Sequence
from kirin import ir
from kirin.dialects.ilist import IList
from kirin.dialects import py, func, ilist
from bloqade.shuttle import gate, init, spec
from bloqade.geometry import grid
from bloqade.shuttle.dialects import gate, filled
from bloqade.shuttle.stdlib.waypoints import move_by_waypoints

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

        x_src = [src[2] for src in sorted_srcs]
        y_src = [src[3] for src in sorted_srcs]
        # assume only address qubits will move
        x_dst = [dst[2] * 2 for dst in sorted_dsts]
        y_dst = [dst[3] * 2 for dst in sorted_dsts]

        x_src_ref = self.push_constant(x_src)
        y_src_ref = self.push_constant(y_src)
        x_dst_ref = self.push_constant(x_dst)
        y_dst_ref = self.push_constant(y_dst)

        # horizontal move
        is_horizontal_move = True
        for x0, x1 in zip(x_src, x_dst):
            if x0 != x1:
                is_horizontal_move = False
                break
        if is_horizontal_move:
            self.entangle_cols(x_src, x_dst)
        else:
            self.entangle_rows(y_src, y_dst)
                
        self.push_stmt(
            func.Invoke(
                inputs=(x_src_ref, y_src_ref, x_dst_ref, y_dst_ref),
                callee=self.move_kernel,
                kwargs=(),
            )
        )
    
    def entangle_cols(self, ctrls: ilist.IList[int, Any], qargs: ilist.IList[int, Any]): 

        # set up zone layout
        entangling_pair_dist = 2.0  
        path_shift_dist = 3.0
        zone = spec.get_static_trap(zone_id="traps") 
        traps_shape = grid.shape(zone) 
        all_rows = ilist.range(traps_shape[1]) 

        src = grid.sub_grid(zone, ctrls, all_rows) 
        dst = grid.sub_grid(zone, qargs, all_rows) 
        path_shift_dist = abs(src - dst)
        # define the moves
        first_waypoint = grid.shift(src, 0.0, -path_shift_dist) 
        second_waypoint = grid.shift(dst, -entangling_pair_dist, -path_shift_dist) 
        third_waypoint = grid.shift(dst, -entangling_pair_dist, 0.0) 

        waypoints = ilist.IList([src, first_waypoint, second_waypoint, third_waypoint])  # need to do push constant and get reference to make it runtime

        move_by_waypoints(waypoints, True, False) 

    def entangle_rows(self, ctrls: ilist.IList[int, Any], qargs: ilist.IList[int, Any]): 

        # set up zone layout
        entangling_pair_dist = 2.0  
        path_shift_dist = 3.0
        traps_shape = grid.shape(self.grid_mapping) 
        all_cols = ilist.range(traps_shape[0]) 

        src = grid.sub_grid(self.grid_mapping, all_cols, ctrls)
        dst = grid.sub_grid(self.grid_mapping, all_cols, qargs)

        # define the moves
        first_waypoint = grid.shift(src, entangling_pair_dist, 0.0) 
        second_waypoint = grid.shift(dst, entangling_pair_dist, 0.0) 

        waypoints = ilist.IList([src, first_waypoint, second_waypoint]) 

        move_by_waypoints(waypoints, True, False) 
        
    def single_zone_move_impl(
        self,
        src_x: IList[int, Any],
        src_y: IList[int, Any],
        dst_x: IList[int, Any],
        dst_y: IList[int, Any],
    ):
        ...

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

        
# todo: make all lists to IList

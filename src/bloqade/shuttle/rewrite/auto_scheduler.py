from dataclasses import dataclass

from kirin import ir
from kirin.rewrite import abc

from bloqade.shuttle.analysis.schedule.lattice import (
    ScheduleLattice,
)


@dataclass
class AutoRewriter(abc.RewriteRule):

    groups: dict[ir.SSAValue, ScheduleLattice]

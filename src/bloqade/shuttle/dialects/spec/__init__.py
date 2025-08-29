from bloqade.shuttle.dialects.spec._interface import (
    get_float_constant as get_float_constant,
    get_int_constant as get_int_constant,
    get_static_trap as get_static_trap,
)

from ._dialect import dialect as dialect
from .concrete import ArchSpecMethods as ArchSpecMethods
from .stmts import (
    GetFloatConstant as GetFloatConstant,
    GetIntConstant as GetIntConstant,
    GetStaticTrap as GetStaticTrap,
)

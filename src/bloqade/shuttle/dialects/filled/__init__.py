from ._dialect import dialect as dialect
from ._interface import (
    fill as fill,
    get_parent as get_parent,
    vacat as vacat,
)
from .concrete import FilledGridMethods as FilledGridMethods
from .stmts import Fill as Fill, GetParent as GetParent, Vacat as Vacat
from .types import FilledGrid as FilledGrid, FilledGridType as FilledGridType

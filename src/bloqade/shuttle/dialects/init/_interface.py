from typing import Any

from bloqade.geometry.dialects import grid
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import Fill


@_wraps(Fill)
def fill(
    locations: ilist.IList[grid.Grid[Any, Any], Any] | list[grid.Grid[Any, Any]],
):
    """Fill the given locations with the given value.

    Args:
        locations (ilist.IList[grid.Grid[Any,Any], Any]): The locations to fill.
            Note that these locations must be valid static trap locations.

    """
    ...

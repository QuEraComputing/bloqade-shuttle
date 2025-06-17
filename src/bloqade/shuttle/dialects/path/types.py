from dataclasses import dataclass, field
from typing import Any

from kirin import types
from kirin.dialects import ilist

from bloqade.shuttle.codegen.taskgen import AbstractAction


@dataclass
class Path:
    x_tones: ilist.IList[int, Any]
    y_tones: ilist.IList[int, Any]
    path: list[AbstractAction] = field(default_factory=list, repr=False)

    def __repr__(self) -> str:
        return f"Path({self.x_tones!r}, {self.y_tones!r}, {self.path!r})"

    def __hash__(self):
        return id(self)


PathType = types.PyClass(Path)

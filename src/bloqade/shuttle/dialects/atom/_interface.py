from typing import Any, TypeVar, overload

from bloqade.geometry.dialects import grid
from bloqade.types import Qubit
from kirin.dialects import ilist
from kirin.lowering import wraps as _wraps

from .stmts import Measure, Move, MoveNextTo, New, ResetPosition
from .types import Atom

NumQubits = TypeVar("NumQubits")


@overload
def new(zone: grid.Grid, qubits: list[Qubit]) -> ilist.IList[Atom, Any]: ...
@overload
def new(
    zone: grid.Grid, qubits: ilist.IList[Qubit, NumQubits]
) -> ilist.IList[Atom, NumQubits]: ...
@_wraps(New)
def new(zone, qubits):
    """
    Create new atoms in the specified zone with the given qubits.

    Args:
        zone (grid.Grid): The grid zone where atoms will be created.
        qubits (list[Qubit] | ilist.IList[Qubit, NumQubits]): The qubits associated with the new atoms.

    Returns:
        ilist.IList[Atom, NumQubits | Any]: A list of newly created atoms.
    """
    ...


NumAtoms = TypeVar("NumAtoms")


@overload
def move(zone: grid.Grid, atoms: list[Atom]) -> ilist.IList[Atom, Any]: ...
@overload
def move(
    zone: grid.Grid, atoms: ilist.IList[Atom, NumAtoms]
) -> ilist.IList[Atom, NumAtoms]: ...
@_wraps(Move)
def move(zone, atoms) -> ilist.IList[Atom, Any]:
    """
    Create new atoms in the specified zone with the given qubits. Note that the specific locations of the atoms will be determined by the compiler.


    Args:
        zone (grid.Grid): The grid zone where to move the atoms.
        atoms (list[Atom] | ilist.IList[Atom, NumQubits]): The atoms to be moved.

    Returns:
        ilist.IList[Atom, NumQubits | Any]: A list of newly created atoms.
    """
    ...


@overload
def move_next_to(
    zone: grid.Grid[Any, Any], ctrls: list[Atom], qargs: list[Atom]
) -> tuple[ilist.IList[Atom, NumAtoms], ilist.IList[Atom, NumAtoms]]: ...
@overload
def move_next_to(
    zone: grid.Grid[Any, Any], ctrls: ilist.IList[Atom, NumAtoms], qargs: list[Atom]
) -> tuple[ilist.IList[Atom, NumAtoms], ilist.IList[Atom, NumAtoms]]: ...
@overload
def move_next_to(
    zone: grid.Grid[Any, Any], ctrls: list[Atom], qargs: ilist.IList[Atom, NumAtoms]
) -> tuple[ilist.IList[Atom, NumAtoms], ilist.IList[Atom, NumAtoms]]: ...
@overload
def move_next_to(
    zone: grid.Grid[Any, Any],
    ctrls: ilist.IList[Atom, NumAtoms],
    qargs: ilist.IList[Atom, NumAtoms],
) -> tuple[ilist.IList[Atom, NumAtoms], ilist.IList[Atom, NumAtoms]]: ...
@_wraps(MoveNextTo)
def move_next_to(zone, ctrls, qargs):
    """
    Apply an operation to the specified atoms, optionally moving them in the process if the gate operation requires it.
    After the operation, the atoms potentially change their positions which will be reflected in the returned list.

    Args:
        zone (grid.Grid[Any, Any]): The grid zone where the atoms are located.
        ctrls (list[Atom] | ilist.IList[Atom, NumAtoms]): The control atoms for the operation.
        qargs (list[Atom] | ilist.IList[Atom, NumAtoms]): The target atoms for the operation.

    Returns:
        tuple[ilist.IList[Atom, NumAtoms], ilist.IList[Atom, NumAtoms]]:
            A tuple containing two lists of atoms: the control atoms and the target atoms after the operation.
            the first list contains the updated ctrls, and the second list contains the updated qargs.
    """
    ...


@overload
def reset_position(atoms: list[Atom], qubits: list[Qubit]) -> None: ...
@overload
def reset_position(atoms: list[Atom], qubits: ilist.IList[Qubit, NumAtoms]) -> None: ...
@overload
def reset_position(atoms: ilist.IList[Atom, NumAtoms], qubits: list[Qubit]) -> None: ...
@overload
def reset_position(
    atoms: ilist.IList[Atom, NumAtoms], qubits: ilist.IList[Qubit, NumAtoms]
) -> None: ...
@_wraps(ResetPosition)
def reset_position(atoms, qubits) -> None:
    """
    Reset the position of atoms to their initial state, terminating the moves.

    Args:
        atoms (list[Atom] | ilist.IList[Atom, NumAtoms]): The atoms whose positions will be reset.
        qubits (list[Qubit] | ilist.IList[Qubit, NumAtoms]): The qubits associated with the atoms being reset.
    """
    ...


@overload
def measure(atoms: list[Atom], qubits: list[Qubit]) -> ilist.IList[int, Any]: ...
@overload
def measure(
    atoms: ilist.IList[Atom, NumAtoms], qubits: list[Qubit]
) -> ilist.IList[int, NumAtoms]: ...
@overload
def measure(
    atoms: list[Atom], qubits: ilist.IList[Qubit, NumAtoms]
) -> ilist.IList[int, NumAtoms]: ...
@overload
def measure(
    atoms: ilist.IList[Atom, NumAtoms], qubits: ilist.IList[Qubit, NumAtoms]
) -> ilist.IList[int, NumAtoms]: ...
@_wraps(Measure)
def measure(atoms, qubits) -> ilist.IList[int, Any]:
    """
    Perform a destructive measurement on the specified atoms.

    Args:
        atoms (list[Atom] | ilist.IList[Atom, NumAtoms]): The atoms to be measured.
        qubits (list[Qubit] | ilist.IList[Qubit, NumAtoms]): The qubits associated with the atoms being measured.

    Returns:
        ilist.IList[int, NumAtoms | Any]: A list of measurement results, where each result corresponds to an atom.
    """
    ...

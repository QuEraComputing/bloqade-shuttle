from bloqade.geometry.dialects.grid import types as zone_types
from kirin import ir, lowering, types
from kirin.decl import info, statement
from kirin.dialects import func, ilist
from kirin.ir import (
    CallableStmtInterface,
    HasSignature,
    IsolatedFromAbove,
    Region,
    Statement,
    SymbolOpInterface,
)
from kirin.print.printer import Printer

from bloqade.shuttle.dialects.action._dialect import dialect


class TweezerFuncOpCallableInterface(CallableStmtInterface["TweezerFunction"]):

    @classmethod
    def get_callable_region(cls, stmt: ir.Statement) -> Region:
        assert isinstance(stmt, TweezerFunction)
        return stmt.body


@statement(dialect=dialect)
class TweezerFunction(Statement):
    name = "move.func"
    traits = frozenset(
        {
            IsolatedFromAbove(),
            SymbolOpInterface(),
            HasSignature(),
            TweezerFuncOpCallableInterface(),
        }
    )
    sym_name: str = info.attribute()
    signature: func.Signature = info.attribute()
    body: Region = info.region(multi=True)

    def print_impl(self, printer: Printer) -> None:
        with printer.rich(style="red"):
            printer.plain_print(self.name + " ")

        with printer.rich(style="cyan"):
            printer.plain_print(self.sym_name)

        self.signature.print_impl(printer)
        printer.plain_print(" ")
        self.body.print_impl(printer)

        with printer.rich(style="black"):
            printer.plain_print(f" // move.func {self.sym_name}")


# this is used as mediate to lower to flair
@statement(dialect=dialect)
class GetXToneId(Statement):
    name = "get.xtoneid"
    traits = frozenset({lowering.FromPythonCall()})
    idx: ir.SSAValue = info.argument(type=types.Int)
    result: ir.ResultValue = info.result(type=types.Int)


# this is used as mediate to lower to flair
@statement(dialect=dialect)
class GetYToneId(Statement):
    name = "get.ytoneid"
    traits = frozenset({lowering.FromPythonCall()})
    idx: ir.SSAValue = info.argument(type=types.Int)
    result: ir.ResultValue = info.result(type=types.Int)


@statement
class IntensityStatement(ir.Statement):
    x_tones: ir.SSAValue = info.argument(
        type=types.Union(
            ilist.IListType[types.Int, types.TypeVar("L")],
            types.Slice[types.Int],
        )
    )
    y_tones: ir.SSAValue = info.argument(
        type=types.Union(
            ilist.IListType[types.Int, types.TypeVar("L")],
            types.Slice[types.Int],
        )
    )


@statement(dialect=dialect)
class TurnOn(IntensityStatement):
    name = "ramp.on"
    traits = frozenset({lowering.FromPythonCall()})


@statement(dialect=dialect)
class TurnOff(IntensityStatement):
    name = "ramp.off"
    traits = frozenset({lowering.FromPythonCall()})


@statement
class IntensityXYSlice(ir.Statement):
    x_tones: ir.SSAValue = info.argument(types.Slice[types.Int])
    y_tones: ir.SSAValue = info.argument(types.Slice[types.Int])


@statement(dialect=dialect)
class TurnOnXYSlice(IntensityXYSlice):
    name = "ramp.on.slice_xy"
    traits = frozenset({})


@statement(dialect=dialect)
class TurnOffXYSlice(IntensityXYSlice):
    name = "ramp.off.slice_xy"
    traits = frozenset({})


@statement
class IntensityXSlice(ir.Statement):
    x_tones: ir.SSAValue = info.argument(types.Slice[types.Int])
    y_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, types.Any])


@statement(dialect=dialect)
class TurnOnXSlice(IntensityXSlice):
    name = "ramp.on.slice_x"
    traits = frozenset({})


@statement(dialect=dialect)
class TurnOffXSlice(IntensityXSlice):
    name = "ramp.off.slice_x"
    traits = frozenset({})


@statement
class IntensityYSlice(ir.Statement):
    x_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, types.Any])
    y_tones: ir.SSAValue = info.argument(types.Slice[types.Int])


@statement(dialect=dialect)
class TurnOnYSlice(IntensityYSlice):
    name = "ramp.on.slice_y"
    traits = frozenset({})


@statement(dialect=dialect)
class TurnOffYSlice(IntensityYSlice):
    name = "ramp.off.slice_y"
    traits = frozenset({})


@statement
class Intensity(ir.Statement):
    x_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, types.Any])
    y_tones: ir.SSAValue = info.argument(ilist.IListType[types.Int, types.Any])


@statement(dialect=dialect)
class TurnOnXY(Intensity):
    name = "ramp.on.xy"
    traits = frozenset({})


@statement(dialect=dialect)
class TurnOffXY(Intensity):
    name = "ramp.off.xy"
    traits = frozenset({})


NxTones = types.TypeVar("NxTones")
NyTones = types.TypeVar("NyTones")


@statement(dialect=dialect)
class Set(Statement):
    # set location
    name = "set"
    traits = frozenset({lowering.FromPythonCall()})
    grid: ir.SSAValue = info.argument(type=zone_types.GridType[NxTones, NyTones])


@statement(dialect=dialect)
class Move(Statement):
    # move to location
    name = "move"
    traits = frozenset({lowering.FromPythonCall()})
    grid: ir.SSAValue = info.argument(type=zone_types.GridType[NxTones, NyTones])

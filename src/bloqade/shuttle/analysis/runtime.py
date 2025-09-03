from dataclasses import dataclass, field

from kirin import interp, ir
from kirin.analysis import ForwardExtra, ForwardFrame, const
from kirin.dialects import func, scf
from kirin.lattice import EmptyLattice


@dataclass
class RuntimeFrame(ForwardFrame[EmptyLattice]):
    """Frame for quantum runtime analysis.
    This frame is used to track the state of quantum operations within a method.
    """

    quantum_stmts: set[ir.Statement] = field(default_factory=set)
    """Set of quantum statements in the frame."""
    is_quantum: bool = False
    """Whether the frame contains quantum operations."""


class RuntimeAnalysis(ForwardExtra[RuntimeFrame, EmptyLattice]):
    """Forward dataflow analysis to check if a method has quantum runtime.

    This analysis checks if a method contains any quantum runtime operations.
    It is used to determine if the method can be executed on a quantum device.
    """

    keys = ["runtime"]
    lattice = EmptyLattice

    def eval_stmt_fallback(self, frame: RuntimeFrame, stmt: ir.Statement):
        return tuple(self.lattice.top() for _ in stmt.results)

    def initialize_frame(
        self, code: ir.Statement, *, has_parent_access: bool = False
    ) -> RuntimeFrame:
        return RuntimeFrame(code, has_parent_access=has_parent_access)

    def run_method(self, method: ir.Method, args: tuple[EmptyLattice, ...]):
        return self.run_callable(method.code, (self.lattice.bottom(),) + args)

    def has_quantum_runtime(self, method: ir.Method) -> bool:
        """Return True if the method has quantum runtime operations, False otherwise."""
        frame, _ = self.run_analysis(method)
        return frame.is_quantum


@scf.dialect.register(key="runtime")
class Scf(interp.MethodTable):

    @interp.impl(scf.IfElse)
    def ifelse(self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: scf.IfElse):
        # If either branch is quantum, the whole ifelse is quantum
        with _interp.new_frame(stmt, has_parent_access=True) as then_frame:
            then_result = _interp.run_ssacfg_region(
                then_frame, stmt.then_body, (_interp.lattice.top(),)
            )

        with _interp.new_frame(stmt, has_parent_access=True) as else_frame:
            else_result = _interp.run_ssacfg_region(
                else_frame, stmt.else_body, (_interp.lattice.top(),)
            )

        frame.is_quantum = (
            frame.is_quantum or then_frame.is_quantum or else_frame.is_quantum
        )
        frame.quantum_stmts.update(then_frame.quantum_stmts, else_frame.quantum_stmts)
        match (then_result, else_result):
            case (interp.ReturnValue(), tuple()):
                return else_result
            case (tuple(), interp.ReturnValue()):
                return then_result
            case (tuple(), tuple()):
                return tuple(
                    then_result.join(else_result)
                    for then_result, else_result in zip(then_result, else_result)
                )
            case _:
                return tuple(_interp.lattice.top() for _ in stmt.results)

    @interp.impl(scf.For)
    def for_loop(self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: scf.For):
        args = (_interp.lattice.top(),) * (len(stmt.initializers) + 1)
        with _interp.new_frame(stmt, has_parent_access=True) as body_frame:
            result = _interp.run_ssacfg_region(
                body_frame, stmt.body, (_interp.lattice.bottom(),)
            )

        frame.is_quantum = frame.is_quantum or body_frame.is_quantum
        frame.quantum_stmts.update(body_frame.quantum_stmts)
        if isinstance(result, interp.ReturnValue) or result is None:
            return args[1:]
        else:
            return tuple(arg.join(res) for arg, res in zip(args[1:], result))

    @interp.impl(scf.Yield)
    def yield_stmt(
        self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: scf.Yield
    ):
        return interp.YieldValue(frame.get_values(stmt.args))


@func.dialect.register(key="runtime")
class Func(interp.MethodTable):

    @interp.impl(func.Invoke)
    def invoke(self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: func.Invoke):
        args = (_interp.lattice.top(),) * len(stmt.inputs)
        callee_frame, result = _interp.run_method(stmt.callee, args)
        frame.is_quantum = frame.is_quantum or callee_frame.is_quantum
        return (result,)

    @interp.impl(func.Call)
    def call(self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: func.Call):
        # Check if the called method is quantum
        callee_result = stmt.callee.hints.get("const")
        args = (_interp.lattice.top(),) * len(stmt.inputs)
        if (
            isinstance(callee_result, const.PartialLambda)
            and (trait := callee_result.code.get_trait(ir.CallableStmtInterface))
            is not None
        ):
            body = trait.get_callable_region(callee_result.code)
            with _interp.new_frame(stmt) as callee_frame:
                result = _interp.run_ssacfg_region(callee_frame, body, args)
        else:
            raise InterruptedError("Dynamic method calls are not supported")

        frame.is_quantum = frame.is_quantum or callee_frame.is_quantum
        return (result,)

    @interp.impl(func.Return)
    def return_stmt(
        self, _interp: RuntimeAnalysis, frame: RuntimeFrame, stmt: func.Return
    ):
        return interp.ReturnValue(frame.get_values(stmt.results))

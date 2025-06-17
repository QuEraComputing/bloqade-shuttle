from bloqade.geometry.dialects import grid
from bloqade.squin import op, qubit
from kirin import ir
from kirin.dialects import func, ilist
from kirin.passes import Default, Fold, TypeInfer
from kirin.prelude import structural
from kirin.rewrite import Walk
from kirin.rewrite.chain import Chain

from bloqade.qourier.dialects import (
    action,
    atom,
    gate,
    init,
    measure,
    path,
    schedule,
    spec,
)
from bloqade.qourier.passes.inject_spec import InjectSpecsPass
from bloqade.qourier.passes.schedule2path import ScheduleToPath
from bloqade.qourier.rewrite.desugar import DesugarTurnOffRewrite, DesugarTurnOnRewrite


@ir.dialect_group(structural.union([spec, grid, atom, gate, op, qubit]))
def kernel(self):
    def run_pass(
        mt: ir.Method,
        *,
        verify: bool = True,
        fold: bool = True,
        aggressive: bool = False,
        typeinfer: bool = True,
        arch_spec: spec.Spec | None = None,
    ) -> None:
        if arch_spec is None:
            arch_spec = spec.Spec()

        InjectSpecsPass(self, arch_spec=arch_spec)(mt)

        Default(
            self,
            verify=verify,
            fold=fold,
            aggressive=aggressive,
            typeinfer=typeinfer,
            no_raise=False,
        )(mt)

    return run_pass


# We dont allow [cf, aod, schedule] appear in move function
@ir.dialect_group(structural.union([action, spec, grid]))
def tweezer(self):
    fold_pass = Fold(self)
    typeinfer_pass = TypeInfer(self)
    default_spec = spec.Spec()  # TODO read this from a file
    # TODO: add validation pass after type inference to check
    #       that the number of xtones and ytones match the decorator
    ilist_desugar = ilist.IListDesugar(self)
    action_desugar_pass = Walk(Chain(DesugarTurnOnRewrite(), DesugarTurnOffRewrite()))

    def run_pass(
        mt: ir.Method,
        *,
        fold: bool = True,
        spec: spec.Spec | None = None,
    ) -> None:
        InjectSpecsPass(self, arch_spec=spec or default_spec)(mt)

        if isinstance(mt.code, func.Function):
            new_code = action.TweezerFunction(
                sym_name=mt.code.sym_name,
                signature=mt.code.signature,
                body=mt.code.body,
            )
            mt.code = new_code
        else:
            raise ValueError("Method code must be a Function, cannot be lambda/closure")

        ilist_desugar.fixpoint(mt)

        typeinfer_pass(mt)
        action_desugar_pass.rewrite(mt.code)

        if fold:
            fold_pass(mt)

    return run_pass


# no action allow. can have cf, with addtional spec
@ir.dialect_group(
    structural.union([init, schedule, path, grid, spec, gate, op, measure])
)
def move(self):
    schedule_to_path = ScheduleToPath(self)

    def run_pass(
        mt: ir.Method,
        *,
        verify: bool = True,
        fold: bool = True,
        aggressive: bool = False,
        typeinfer: bool = True,
        arch_spec: spec.Spec | None = None,
    ) -> None:
        if arch_spec is not None:
            InjectSpecsPass(self, arch_spec=arch_spec, fold=False)(mt)

        schedule_to_path(mt)

        Default(
            self,
            verify=verify,
            fold=fold,
            aggressive=aggressive,
            typeinfer=typeinfer,
            no_raise=False,
        )(mt)

    return run_pass

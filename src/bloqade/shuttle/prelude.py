from bloqade.geometry.dialects import grid
from bloqade.squin import op, qubit
from kirin import ir
from kirin.dialects import func, ilist
from kirin.passes import Default, Fold, TypeInfer
from kirin.prelude import structural
from kirin.rewrite import Walk
from kirin.rewrite.chain import Chain

from bloqade.shuttle import spec as spec_module
from bloqade.shuttle.dialects import (
    action,
    atom,
    filled,
    gate,
    init,
    measure,
    path,
    schedule,
    spec,
)
from bloqade.shuttle.passes.inject_spec import InjectSpecsPass
from bloqade.shuttle.passes.schedule2path import ScheduleToPath
from bloqade.shuttle.rewrite.desugar import DesugarTurnOffRewrite, DesugarTurnOnRewrite


@ir.dialect_group(structural.union([spec, grid, filled, atom, gate, op, qubit]))
def kernel(self):
    def run_pass(
        mt: ir.Method,
        *,
        verify: bool = True,
        fold: bool = True,
        aggressive: bool = False,
        typeinfer: bool = True,
        arch_spec: spec_module.ArchSpec | None = None,
    ) -> None:
        if arch_spec is not None:
            InjectSpecsPass(self, arch_spec=arch_spec, fold=False)(mt)

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
@ir.dialect_group(structural.union([action, spec, grid, filled]))
def tweezer(self):
    fold_pass = Fold(self)
    typeinfer_pass = TypeInfer(self)
    # TODO: add validation pass after type inference to check
    #       that the number of xtones and ytones match the decorator
    ilist_desugar = ilist.IListDesugar(self)
    action_desugar_pass = Walk(Chain(DesugarTurnOnRewrite(), DesugarTurnOffRewrite()))

    def run_pass(
        mt: ir.Method,
        *,
        fold: bool = True,
        arch_spec: spec_module.ArchSpec | None = None,
    ) -> None:
        if arch_spec is not None:
            InjectSpecsPass(self, arch_spec=arch_spec, fold=False)(mt)

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
    structural.union([init, schedule, path, grid, filled, spec, gate, op, measure])
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
        arch_spec: spec_module.ArchSpec | None = None,
    ) -> None:
        schedule_to_path(mt)

        if arch_spec is not None:
            InjectSpecsPass(self, arch_spec=arch_spec, fold=False)(mt)

        Default(
            self,
            verify=verify,
            fold=fold,
            aggressive=aggressive,
            typeinfer=typeinfer,
            no_raise=False,
        )(mt)

    return run_pass

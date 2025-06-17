from bloqade.geometry.dialects import grid

from bloqade.qourier.dialects import spec
from bloqade.qourier.stdlib.spec import single_zone_spec


def test_single_zone_spec():
    arch_spec = single_zone_spec(3, 3, 10.0)

    expected_spec = spec.Spec(
        layout=spec.Layout(
            static_traps={
                "traps": grid.Grid(
                    x_spacing=(10.0, 10.0),
                    y_spacing=(10.0, 10.0),
                    x_init=0.0,
                    y_init=0.0,
                )
            },
            fillable=set(["traps"]),
        )
    )

    assert (
        arch_spec == expected_spec
    ), "The generated spec does not match the expected spec."

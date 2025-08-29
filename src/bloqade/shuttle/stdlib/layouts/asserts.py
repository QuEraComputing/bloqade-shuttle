from bloqade.shuttle.prelude import tweezer


@tweezer
def assert_sorted(indices):
    for i in range(1, len(indices)):
        assert indices[i - 1] < indices[i], "Indices must be sorted in ascending order."

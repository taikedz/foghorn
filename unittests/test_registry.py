from registry import sort_rows


class TestRegistryHelpers:
    def test_sort_rows(self):
        raw_rows = [
            [(45,67), "triple", "b"], # 112
            [(3,2), "single", "b"], # 5
            [(7,7), "double", "a"], # 14
            [(6,7), "double", "c"], # 13
            [(4,5), "single", "d"], # 9
        ]
        res = sort_rows(raw_rows, organise_on=1, sort_on=(0, sum))

        assert res == [
            [(6,7), "double", "c"], # 13
            [(7,7), "double", "a"], # 14
            [(3,2), "single", "b"], # 5
            [(4,5), "single", "d"], # 9
            [(45,67), "triple", "b"], # 112
        ]
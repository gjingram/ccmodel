import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_namespace
class TestCCModelNamespace(CCModelTest):
    parse_state = ParseHeader("namespace_test.hh", "namespace_test", [])

    def test_parse_objects_exist(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        pdb.set_trace()
        print(f"{''.join([key + os.linesep for key in summary.identifier_map.keys()])}")
        expected_keys = [
            "GlobalNamespace",
            "::TestAnonNested1",
            "TestNamespace1",
            "TestNested1",
            "TestNested1::TestNested2",
        ]
        for key in expected_keys:
            assert summary.name_in_summary(key)

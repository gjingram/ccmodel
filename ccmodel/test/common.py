import pathlib
import os
import pdb
import pytest

from typing import Dict, List

from ..parsers import cpp_parse as parser
from ..utils import summary as summary


class ParseHeader(object):
    def __init__(self, test_file: str, unit_name: str, parse_also: List[str]):
        self.test_file = os.path.join("test_hh", test_file)
        self.unit_name = unit_name
        self.test_dir = str(pathlib.Path(os.path.dirname(os.path.realpath(__file__))))
        self.test_file_abs = os.path.join(self.test_dir, self.test_file)
        self.loc = os.path.join(self.test_dir, "test_out")

        parser.set_working_directory(self.test_dir)
        parser.set_save_dir(self.loc)
        parser.set_unit_name(self.unit_name)
        for p_also in parse_also:
            parser.include(p_also)
        parser.add_header(self.test_file)
        parser.set_compiler_args(["-x", "c++", "-std=c++11"])
        parser.process_headers()

        return

    def load_parse_state(self) -> "ParserSummary":
        return summary.load_summary(self.unit_name + ".ccms", loc=self.loc)


class CCModelTest(object):
    parse_state = None

    @pytest.fixture
    def cls_type(self):
        return type(self)

    @pytest.fixture
    def lps(self, cls_type):
        return cls_type.parse_state.load_parse_state()

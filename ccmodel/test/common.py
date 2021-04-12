import pathlib
import os
import pdb
import pytest

from typing import Dict

from ..parsers import cpp_parse as cppp
from ..utils import summary as summary

ClangParseCpp = cppp.ClangParseCpp


class ParseHeader(object):

    def __init__(self, test_file: str, unit_name: str):
        self.test_file = os.path.join("test_hh", test_file)
        self.unit_name = unit_name
        self.test_dir = str(pathlib.Path(os.path.dirname(os.path.realpath(__file__))))
        self.test_file_abs = os.path.join(self.test_dir, self.test_file)
        self.loc = os.path.join(self.test_dir, "test_out")

        parser = ClangParseCpp(self.test_dir, self.loc, self.unit_name)
        parser.add_header(self.test_file)
        parser.compiler_args = "-x c++ -std=c++11"
        parser.process_headers()

        return

    def load_parse_state(self) -> Dict[str, "summary.HeaderSummary"]:
        return summary.load_summary(self.unit_name + ".ccms", loc=self.loc)


class CCModelTest(object):
    parse_state = None

    @pytest.fixture
    def cls_type(self):
        return type(self)

    @pytest.fixture
    def lps(self, cls_type):
        return cls_type.parse_state.load_parse_state()

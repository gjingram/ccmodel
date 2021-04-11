import pytest
import pathlib
import os
import pdb

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

    def load_parse_state(self) -> Dict[str, 'summary.HeaderSummary']:
        return summary.load_summary(self.unit_name + ".ccms", loc=self.loc)


class TestCCModelParseTest(object):
    parse_state = ParseHeader("parse_test.hh", "parse_test")
   
    @pytest.fixture(scope='class', autouse=True)
    def cls_type(self):
        return type(self)

    @pytest.fixture(scope='class', autouse=True)
    def lps(self, cls_type):
        return cls_type.parse_state.load_parse_state()

    def test_header_in_state(cls_type, lps):
        assert cls_type.parse_state.test_file_abs in lps

    def test_parse_objects_exist(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        pdb.set_trace()
        print(f"{''.join([key + os.linesep for key in summary.identifier_map.keys()])}")
        expected_keys = [
                "GlobalNamespace",
                "testEnum1",
                "testEnum1::A",
                "testEnum1::B",
                "testEnum2",
                "testEnum2::A",
                "testEnum2::B",
                "testFunc1(double, float, int)",
                "testFunc1(double, float, int)::param0",
                "testFunc1(double, float, int)::a",
                "testFunc1(double, float, int)::b",
                "testFunc1(int, float, double)",
                "testFunc1(int, float, double)::param0",
                "testFunc1(int, float, double)::param1",
                "testFunc1(int, float, double)::a",
                "testFunc1(double *, double &)",
                "testFunc1(double *, double &)::param0",
                "testFunc1(double *, double &)::param1",
                "var",
                "statVar",
                "etherStateVar",
                "testNamespace1",
                "testNamespace1::var1",
                "testNamespace1::testNamespace2",
                "testNamespace1::testNamespace2::var",
                "doubleVec",
                "floatVec",
                "ttNamespace1",
                ":USING: using std::vector",
                "std::vector<~, ~>",
                ":USING: using namespace testNamespace1::testNamespace2",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>::O",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>::A",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>::n",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>::b",
                "testTemplateFunction<~, ~, size_t~, size_t[1], [~...]>::var",
                "testTemplateFunction(A&)::classIn",
                "testTemplateFunction(A&)",
                "TestCStruct",
                "TestCStruct::a1",
                "TestCStruct::a2",
                "TestCStruct::a3",
                "TestCppStruct",
                "TestCppStruct::b1",
                "TestCppStruct::b2",
                "TestCppStruct::b3",
                "TestCppStruct::TestCppStruct()",
                "TestCppStruct::~TestCppStruct()",
                "TestCppClass",
                "TestCppClass::TestCppClass()",
                "TestCppClass::TestCppClass(double)",
                "TestCppClass::TestCppClass(double)::param0",
                "TestCppClass::~TestCppClass()",
                "TestCppClass::testMethod1(TestCppClass &) const",
                "TestCppClass::testMethod1(TestCppClass &)::param0",
                "TestCppClass::testMethod2(float)",
                "TestCppClass::testMethod2(float)::param0",
                "TestCppClass::testMethod3()",
                "TestCppClass::t",
                "TestCppClass::testMethod1()",
                "TestTemplateClass1<~, ~>",
                "TestTemplateClass1<~, ~>::TestTemplateClass1()",
                "TestTemplateClass1<~, ~>::~TestTemplateClass1()",
                "TestTemplateClass1<~, ~>::testMethod3()",
                "TestTemplateClass1<~, ~>::testMethod4<~>(A&)",
                "TestTemplateClass1<~, ~>::testMethod5(B&)",
                "TestTemplateClass1<~>",
                "TestTemplateClass1<~>::TestTemplateClass1()",
                "TestTemplateClass1<~>::~TestTemplateClass1()",
                "TestTemplateClass1<~>::test_spec_func()",
                "testPartial<~>",
                "TestCppClass2",
                "TestCppClass2::TestCppClass2",
                "TestCppClass2::~TestCppClass2"
                ]
        pdb.set_trace()
        for key in expected_keys:
            assert summary.name_in_summary(key)

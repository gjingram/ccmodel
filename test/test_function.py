import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_function
class TestCCModelFunction(CCModelTest):
    parse_state = ParseHeader("function_test.hh", "function_test", [])

    def test_parse_objects_exist(cls_type, lps):
        summary = lps

        expected = [
            "testFunction1()",
            "testFunction2(double &)",
            "testFunction2(double &)::param0",
            "testFunction3(double, float)",
            "testFunction3(double, float)::param0",
            "testFunction3(double, float)::param1",
            "testFunction3(double *, double **, float&)",
            "testFunction3(double *, double **, float&)::param0",
            "testFunction3(double *, double **, float&)::param1",
            "testFunction3(double *, double **, float&)::param2",
            "testFunction4(int)",
            "testFunction4(int)::param0",
            "testFunction5()",
            "testFunction6(double)",
            "testFunction6(double)::param0",
            "testFunction7(float, float, float)",
            "testFunction7(float, float, float)::a",
            "testFunction7(float, float, float)::b",
            "testFunction7(float, float, float)::c",
            "Nest1",
            "Nest1::testFunction8()",
            "Nest1::Nest2",
            "Nest1::Nest2::testFunction9()",
        ]
        for exp in expected:
            assert summary.name_in_summary(exp)

    def test_functions(cls_type, lps):
        summary = lps

        func1 = summary["testFunction1()"]
        assert func1["id"] == "testFunction1"
        assert func1["scoped_id"] == "testFunction1"
        assert func1["scoped_displayname"] == "testFunction1()"
        assert func1["return"] == "double"
        assert func1["storage_class"] == "NONE"
        assert func1["linkage"] == "EXTERNAL"
        assert func1["n_params"] == 0
        assert func1["type"] == "double ()"

        func2 = summary["testFunction2(double &)"]
        assert func2["id"] == "testFunction2"
        assert func2["scoped_id"] == "testFunction2"
        assert func2["scoped_displayname"] == "testFunction2(double &)"
        assert func2["return"] == "void *"
        assert func2["storage_class"] == "NONE"
        assert func2["linkage"] == "EXTERNAL"
        assert func2["n_params"] == 1
        assert func2["type"] == "void *(double &)"

        func2_param0 = summary["testFunction2(double &)::param0"]
        assert func2_param0["id"] == "param0"
        assert func2_param0["scoped_id"] == "testFunction2::param0"
        assert func2_param0["scoped_displayname"] == "testFunction2(double &)::param0"
        assert func2_param0["usr"] == "testFunction2(double &)::param0"
        assert func2_param0["type"] == "double &"

        func3_0 = summary["testFunction3(double, float)"]
        assert func3_0["id"] == "testFunction3"
        assert func3_0["scoped_id"] == "testFunction3"
        assert func3_0["scoped_displayname"] == "testFunction3(double, float)"
        assert func3_0["return"] == "float"
        assert func3_0["storage_class"] == "NONE"
        assert func3_0["linkage"] == "EXTERNAL"
        assert func3_0["n_params"] == 2

        func3_0_param0 = summary["testFunction3(double, float)::param0"]
        assert func3_0_param0["id"] == "param0"
        assert func3_0_param0["scoped_id"] == "testFunction3::param0"
        assert (
            func3_0_param0["scoped_displayname"]
            == "testFunction3(double, float)::param0"
        )
        assert func3_0_param0["usr"] == "testFunction3(double, float)::param0"
        assert func3_0_param0["type"] == "double"

        func3_0_param1 = summary["testFunction3(double, float)::param1"]
        assert func3_0_param1["id"] == "param1"
        assert func3_0_param1["scoped_id"] == "testFunction3::param1"
        assert (
            func3_0_param1["scoped_displayname"]
            == "testFunction3(double, float)::param1"
        )
        assert func3_0_param1["usr"] == "testFunction3(double, float)::param1"
        assert func3_0_param1["type"] == "float"

        func3_1 = summary["testFunction3(double *, double **, float&)"]
        assert func3_1["id"] == "testFunction3"
        assert func3_1["scoped_id"] == "testFunction3"
        assert (
            func3_1["scoped_displayname"]
            == "testFunction3(double *, double **, float &)"
        )
        assert func3_1["return"] == "void"
        assert func3_1["storage_class"] == "NONE"
        assert func3_1["linkage"] == "EXTERNAL"
        assert func3_1["n_params"] == 3
        assert func3_1["type"] == "void (double *, double **, float &)"

        func4 = summary["testFunction4(int)"]
        assert func4["id"] == "testFunction4"
        assert func4["scoped_id"] == "testFunction4"
        assert func4["scoped_displayname"] == "testFunction4(int)"
        assert func4["return"] == "std::vector<double>"
        assert func4["storage_class"] == "NONE"
        assert func4["linkage"] == "EXTERNAL"
        assert func4["n_params"] == 1
        assert func4["type"] == "std::vector<double> (int)"

        func5 = summary["testFunction5()"]
        assert func5["id"] == "testFunction5"
        assert func5["scoped_id"] == "testFunction5"
        assert func5["scoped_displayname"] == "testFunction5()"
        assert func5["return"] == "void"
        assert func5["storage_class"] == "EXTERN"
        assert func5["linkage"] == "EXTERNAL"
        assert func5["n_params"] == 0
        assert func5["type"] == "void ()"

        func6 = summary["testFunction6(double)"]
        assert func6["id"] == "testFunction6"
        assert func6["scoped_id"] == "testFunction6"
        assert func6["scoped_displayname"] == "testFunction6(double)"
        assert func6["return"] == "void"
        assert func6["storage_class"] == "STATIC"
        assert func6["linkage"] == "INTERNAL"
        assert func6["n_params"] == 1
        assert func6["type"] == "void (double)"

        func7 = summary["testFunction7(float, float, float)"]
        assert func7["id"] == "testFunction7"
        assert func7["scoped_id"] == "testFunction7"
        assert func7["scoped_displayname"] == "testFunction7(float, float, float)"
        assert func7["return"] == "double"
        assert func7["storage_class"] == "NONE"
        assert func7["linkage"] == "EXTERNAL"
        assert func7["n_params"] == 3
        assert func7["type"] == "double (float, float, float)"

        func7_a = summary["testFunction7(float, float, float)::a"]
        assert func7_a["id"] == "a"
        assert func7_a["scoped_id"] == "testFunction7::a"
        assert func7_a["scoped_displayname"] == "testFunction7(float, float, float)::a"
        assert func7_a["usr"] == "testFunction7(float, float, float)::a"
        assert func7_a["type"] == "float"

        func7_b = summary["testFunction7(float, float, float)::b"]
        assert func7_b["id"] == "b"
        assert func7_b["scoped_id"] == "testFunction7::b"
        assert func7_b["scoped_displayname"] == "testFunction7(float, float, float)::b"
        assert func7_b["usr"] == "testFunction7(float, float, float)::b"
        assert func7_b["type"] == "float"

        func7_c = summary["testFunction7(float, float, float)::c"]
        assert func7_c["id"] == "c"
        assert func7_c["scoped_id"] == "testFunction7::c"
        assert func7_c["scoped_displayname"] == "testFunction7(float, float, float)::c"
        assert func7_c["usr"] == "testFunction7(float, float, float)::c"
        assert func7_c["type"] == "float"
        assert func7_c["default"] == str(2)

        func8 = summary["Nest1::testFunction8()"]
        assert func8["id"] == "testFunction8"
        assert func8["scoped_id"] == "Nest1::testFunction8"
        assert func8["scoped_displayname"] == "Nest1::testFunction8()"
        assert func8["return"] == "void"
        assert func8["storage_class"] == "NONE"
        assert func8["linkage"] == "EXTERNAL"
        assert func8["n_params"] == 0
        assert func8["type"] == "void ()"

        func9 = summary["Nest1::Nest2::testFunction9()"]
        assert func9["id"] == "testFunction9"
        assert func9["scoped_id"] == "Nest1::Nest2::testFunction9"
        assert func9["scoped_displayname"] == "Nest1::Nest2::testFunction9()"
        assert func9["return"] == "double"
        assert func9["storage_class"] == "NONE"
        assert func9["linkage"] == "EXTERNAL"
        assert func9["n_params"] == 0
        assert func9["type"] == "double ()"

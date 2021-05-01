import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_variable
class TestCCModelVariable(CCModelTest):
    parse_state = ParseHeader("variable_test.hh", "variable_test", [])

    def test_parse_object_exists(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        print(f"{''.join([key + os.linesep for key in summary.identifier_map.keys()])}")
        expected = ["var1", "var2", "var3", "var4", "var5", "var6", "var7"]
        for key in expected:
            assert summary.name_in_summary(key)

    def test_variable_data(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        var1 = summary["var1"]
        assert var1["storage_class"] == "NONE"
        assert var1["type"] == "double"
        assert var1["is_member"] == False
        assert var1["is_const"] == False
        assert var1["id"] == "var1"
        assert var1["scoped_id"] == "var1"
        assert var1["scoped_displayname"] == "var1"

        var2 = summary["var2"]
        assert var2["storage_class"] == "NONE"
        assert var2["type"] == "float"
        assert var2["is_member"] == False
        assert var2["is_const"] == False
        assert var2["id"] == "var2"
        assert var2["scoped_id"] == "var2"
        assert var2["scoped_displayname"] == "var2"

        var3 = summary["var3"]
        assert var3["storage_class"] == "NONE"
        assert var3["type"] == "std::vector<double>"
        assert var3["is_member"] == False
        assert var3["is_const"] == False
        assert var3["id"] == "var3"
        assert var3["scoped_id"] == "var3"
        assert var3["scoped_displayname"] == "var3"

        var4 = summary["var4"]
        assert var4["storage_class"] == "NONE"
        assert var4["type"] == "void *"
        assert var4["is_member"] == False
        assert var4["is_const"] == False
        assert var4["id"] == "var4"
        assert var4["scoped_id"] == "var4"
        assert var4["scoped_displayname"] == "var4"

        var5 = summary["var5"]
        assert var5["storage_class"] == "NONE"
        assert var5["type"] == "int [3]"
        assert var5["is_member"] == False
        assert var5["is_const"] == False
        assert var5["id"] == "var5"
        assert var5["scoped_id"] == "var5"
        assert var5["scoped_displayname"] == "var5"

        var6 = summary["var6"]
        assert var6["storage_class"] == "NONE"
        assert var6["type"] == "bool **"
        assert var6["is_member"] == False
        assert var6["is_const"] == False
        assert var6["id"] == "var6"
        assert var6["scoped_id"] == "var6"
        assert var6["scoped_displayname"] == "var6"

        var7 = summary["var7"]
        assert var7["storage_class"] == "NONE"
        assert var7["type"] == "std::vector<std::vector<double>>"
        assert var7["is_member"] == False
        assert var7["is_const"] == False
        assert var7["id"] == "var7"
        assert var7["scoped_id"] == "var7"
        assert var7["scoped_displayname"] == "var7"

        var8 = summary["var8"]
        assert var8["storage_class"] == "NONE"
        assert var8["type"] == "double [3][3]"
        assert var8["is_member"] == False
        assert var8["is_const"] == False
        assert var8["id"] == "var8"
        assert var8["scoped_id"] == "var8"
        assert var8["scoped_displayname"] == "var8"

        var9 = summary["::var9"]
        assert var9["storage_class"] == "NONE"
        assert var9["type"] == "float"
        assert var9["is_member"] == False
        assert var9["is_const"] == False
        assert var9["id"] == "var9"
        assert var9["scoped_id"] == "::var9"
        assert var9["scoped_displayname"] == "::var9"

        var10 = summary["Nest1::Nest2::var10"]
        assert var10["storage_class"] == "STATIC"
        assert var10["type"] == "bool"
        assert var10["is_member"] == False
        assert var10["is_const"] == False
        assert var10["id"] == "var10"
        assert var10["scoped_id"] == "Nest1::Nest2::var10"
        assert var10["scoped_displayname"] == "Nest1::Nest2::var10"

        var11 = summary["Nest1::Nest2::var11"]
        assert var11["storage_class"] == "NONE"
        assert var11["type"] == "const double"
        assert var11["is_member"] == False
        assert var11["is_const"] == True
        assert var11["id"] == "var11"
        assert var11["scoped_id"] == "Nest1::Nest2::var11"
        assert var11["scoped_displayname"] == "Nest1::Nest2::var11"

        var12 = summary["Nest1::Nest2::var12"]
        assert var12["storage_class"] == "NONE"
        assert var12["type"] == "const double *"
        assert var12["is_member"] == False
        assert var12["is_const"] == False
        assert var12["id"] == "var12"
        assert var12["scoped_id"] == "Nest1::Nest2::var12"
        assert var12["scoped_displayname"] == "Nest1::Nest2::var12"

        var13 = summary["Nest1::Nest2::var13"]
        assert var13["storage_class"] == "NONE"
        assert var13["type"] == "double *const"
        assert var13["is_member"] == False
        assert var13["is_const"] == True
        assert var13["id"] == "var13"
        assert var13["scoped_id"] == "Nest1::Nest2::var13"
        assert var13["scoped_displayname"] == "Nest1::Nest2::var13"

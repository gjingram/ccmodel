import pytest
import os
import pdb

from .common import ParseHeader, CCModelTest


@pytest.mark.test_templates
class TestCCModelTemplates(CCModelTest):
    parse_state = ParseHeader("templates_test.hh", "templates_test", [])

    def test_objects_in_summary(cls_type, lps):
        summary = lps

        pdb.set_trace()
        expected = [
            "testFunction1(#&)",
            "testFunction1(#&)::param0",
            "testFunction1(#&)::A",
            "testFunction2(#, #*)",
            "testFunction2(#, #*)::param0",
            "testFunction2(#, #*)::param1",
            "testFunction2(#, #*)::A",
            "testFunction2(#, #*)::B",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::A",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::B",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::C",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::n",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::l",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::var",
            (
                "TestTemplateClass1<#, #, #, int #, [true], [#...]>::"
                + "TestTemplateClass1<#, #, #, int #, [true], [#...]>()"
            ),
            (
                "TestTemplateClass1<#, #, #, int #, [true], [#...]>::"
                + "~TestTemplateClass1<#, #, #, int #, [true], [#...]>()"
            ),
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::m1",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::m2",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::m3",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::m4",
            "TestTemplateClass1<#, #, #, int #, [true], [#...]>::m5",
            "TestTemplateClass1<#, #, double, 2>",
            "TestTemplateClass1<#, #, double, 2>::A",
            "TestTemplateClass1<#, #, double, 2>::B",
            "TestTemplateClass1<#, #, double, 2>::TestTemplateClass1<#, #, double, 2>()",
            "TestTemplateClass1<#, #, double, 2>::~TestTemplateClass1<#, #, double, 2>()",
            "TestTemplateClass2<#>",
            "TestTemplateClass2<#>::A",
            "TestTemplateClass2<#>::TestTemplateClass2<#>()",
            "TestTemplateClass2<#>::~TestTemplateClass2<#>()",
            "TestTemplateClass1<#, TestTemplateClass2, double, 2>",
            "TestTemplateClass1<#, TestTemplateClass2, double, 2>::A",
            (
                "TestTemplateClass1<#, TestTemplateClass2, double, 2>::"
                + "TestTemplateClass1<#, TestTemplateClass2, double, 2>()"
            ),
            (
                "TestTemplateClass1<#, TestTemplateClass2, double, 2>::"
                + "~TestTemplateClass1<#, TestTemplateClass2, double, 2>()"
            ),
        ]
        for exp in expected:
            assert summary.name_in_summary(exp)

    def test_templates(cls_type, lps):
        summary = lps

        pdb.set_trace()
        global_ns = summary["GlobalNamespace"]

        tm1 = summary["testFunction1(#&)"]
        assert type(tm1).__name__ == "TemplateObject"
        assert tm1["id"] == "testFunction1"
        assert tm1["scoped_id"] == "testFunction1"
        assert tm1["scoped_displayname"] == "testFunction1(# &)"
        assert not tm1["is_alias"]
        assert tm1["n_template_parameters"] == 1
        assert tm1["template_ref"] is None
        assert tm1["is_primary"]
        assert not tm1["is_partial"]
        assert tm1["primary_ref"] is tm1
        assert not tm1["is_method_template"]
        assert tm1["is_function_template"]
        assert "A" in tm1["template_parameters"]
        assert tm1["scope"] is global_ns

        tm1_func = tm1["object"]
        assert type(tm1_func).__name__ == "FunctionObject"
        assert tm1_func["id"] == "testFunction1"
        assert tm1_func["scoped_id"] == "testFunction1"
        assert tm1_func["scoped_displayname"] == "testFunction1(A &)"
        assert tm1_func["return"] == "void"
        assert tm1_func["storage_class"] == "INVALID"
        assert tm1_func["linkage"] == "EXTERNAL"
        assert tm1_func["n_params"] == 1
        assert tm1_func["type"] == "void (A &)"
        assert tm1_func["scope"] is global_ns

        tm2 = summary["testFunction2(#, #*)"]
        assert type(tm2).__name__ == "TemplateObject"
        assert tm2["id"] == "testFunction2"
        assert tm2["scoped_id"] == "testFunction2"
        assert tm2["scoped_displayname"] == "testFunction2(#, # *)"
        assert not tm2["is_alias"]
        assert tm2["n_template_parameters"] == 2
        assert tm2["template_ref"] is None
        assert tm2["is_primary"]
        assert not tm2["is_partial"]
        assert tm2["primary_ref"] == tm2
        assert not tm2["is_method_template"]
        assert tm2["is_function_template"]
        assert "A" in tm2["template_parameters"]
        assert "B" in tm2["template_parameters"]
        assert tm2["scope"] is global_ns

        tm2_func = tm2["object"]
        assert type(tm2_func).__name__ == "FunctionObject"
        assert tm2_func["id"] == "testFunction2"
        assert tm2_func["scoped_id"] == "testFunction2"
        assert tm2_func["scoped_displayname"] == "testFunction2(A, B *)"
        assert tm2_func["return"] == "A &"
        assert tm2_func["storage_class"] == "INVALID"
        assert tm2_func["linkage"] == "EXTERNAL"
        assert tm2_func["n_params"] == 2
        assert tm2_func["type"] == "A &(A, B *)"
        assert tm2_func["scope"] is global_ns

        tc1 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>"]
        assert type(tc1).__name__ == "TemplateObject"
        assert tc1["id"] == "TestTemplateClass1"
        assert tc1["scoped_id"] == "TestTemplateClass1"
        assert (
            tc1["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>"
        )
        assert tc1["is_primary"]
        assert not tc1["is_partial"]
        assert tc1["template_ref"] is None
        assert tc1["n_template_parameters"] == 6
        assert tc1["primary_ref"] is tc1
        assert not tc1["is_method_template"]
        assert not tc1["is_function_template"]
        assert tc1["scope"] is global_ns

        c1 = tc1["object"]
        assert type(c1).__name__ == "ClassObject"
        assert c1["id"] == "TestTemplateClass1"
        assert c1["scoped_id"] == "TestTemplateClass1"
        assert c1["scoped_displayname"] == "TestTemplateClass1<A, B, C, n, l, var>"
        assert c1["scope"] is global_ns

        c1m1 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>::m1"]
        assert type(c1m1).__name__ == "MemberObject"
        assert c1m1["id"] == "m1"
        assert c1m1["scoped_id"] == "TestTemplateClass1::m1"
        assert (
            c1m1["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>::m1"
        )
        assert c1m1["type"] == "A"
        assert c1m1 in c1["variables"].values()
        assert c1m1["scope"] is c1

        c1m2 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>::m2"]
        assert type(c1m2).__name__ == "MemberObject"
        assert c1m2["id"] == "m2"
        assert c1m2["scoped_id"] == "TestTemplateClass1::m2"
        assert (
            c1m2["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>::m2"
        )
        assert c1m2["type"] == "B<C> *"
        assert c1m2 in c1["variables"].values()
        assert c1m2["scope"] is c1

        c1m3 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>::m3"]
        assert type(c1m3).__name__ == "MemberObject"
        assert c1m3["id"] == "m3"
        assert c1m3["scoped_id"] == "TestTemplateClass1::m3"
        assert (
            c1m3["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>::m3"
        )
        assert c1m3["type"] == "C &"
        assert c1m3 in c1["variables"].values()
        assert c1m3["scope"] is c1

        c1m4 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>::m4"]
        assert type(c1m4).__name__ == "MemberObject"
        assert c1m4["id"] == "m4"
        assert c1m4["scoped_id"] == "TestTemplateClass1::m4"
        assert (
            c1m4["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>::m4"
        )
        assert c1m4["type"] == "int"
        assert c1m4 in c1["variables"].values()
        assert c1m4["scope"] is c1

        c1m5 = summary["TestTemplateClass1<#,#,#,int#,[true],[#...]>::m5"]
        assert type(c1m5).__name__ == "MemberObject"
        assert c1m5["id"] == "m5"
        assert c1m5["scoped_id"] == "TestTemplateClass1::m5"
        assert (
            c1m5["scoped_displayname"]
            == "TestTemplateClass1<#, #, #, int#, [true], [#...]>::m5"
        )
        assert c1m5["type"] == "bool"
        assert c1m5 in c1["variables"].values()
        assert c1m5["scope"] is c1

        pdb.set_trace()

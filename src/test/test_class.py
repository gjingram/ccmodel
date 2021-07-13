import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_class
class TestCCModelClass(CCModelTest):
    parse_state = ParseHeader("class_test.hh", "class_test", [])

    def test_objects_in_summary(cls_type, lps):
        summary = lps

        expected = [
            "TestStruct1",
            "TestStruct1::a1",
            "TestStruct1::a2",
            "TestStruct1::a3",
            "TestStruct2",
            "TestStruct2::a1",
            "TestStruct2::a2",
            "TestStruct2::a3",
            "TestStruct2::TestStruct2()",
            "TestStruct2::TestStruct2(int)",
            "TestStruct2::~TestStruct2()",
            "TestStruct2::testMethod1()",
            "TestStruct2::testMethod2(std::string)",
            "TestStruct2::testMethod3(int)",
            "TestClass1",
            "TestClass1::TestClass1()",
            "TestClass1::TestClass1(double)",
            "TestClass1::~TestClass1()",
            "TestClass1::u1",
            "TestClass1::u2",
            "TestClass1::TEST_ENUM1",
            "TestClass1::TEST_ENUM2",
            "TestClass1::tdef_type::s1",
            "TestClass1::tdef_type::s2",
            "TestClass1::tdef_type",
            "TestClass1::NestedClass1",
            "TestClass1::NestedClass1::NestedClass1()",
            "TestClass1::NestedClass1::~NestedClass1()",
            "TestClass1::NestedClass1::n1",
            "TestClass1::NestedClass1::testMethod1()",
            "TestClass1::b1",
            "TestClass1::b2",
            "TestClass1::b3",
            "TestClass1::testMethod4()",
            "TestClass1::t1",
            "TestClass1::t2",
            "TestClass1::testMethod5(std::string, std::vector<double>&)",
            "TestClass2",
            "TestClass2::TestClass2()",
            "TestClass2::~TestClass2()",
        ]
        for exp in expected:
            assert summary.name_in_summary(exp)

    def test_classes(cls_type, lps):
        summary = lps

        struct1 = summary["TestStruct1"]
        assert type(struct1).__name__ == "ClassObject"
        assert struct1["id"] == "TestStruct1"
        assert struct1["scoped_id"] == "TestStruct1"
        assert struct1["scoped_displayname"] == "TestStruct1"

        s1a1 = summary["TestStruct1::a1"]
        assert type(s1a1).__name__ == "MemberObject"
        assert s1a1["id"] == "a1"
        assert s1a1["scoped_id"] == "TestStruct1::a1"
        assert s1a1["scoped_displayname"] == "TestStruct1::a1"
        assert s1a1["type"] == "double"
        assert s1a1["scope"] is struct1

        s1a2 = summary["TestStruct1::a2"]
        assert type(s1a2).__name__ == "MemberObject"
        assert s1a2["id"] == "a2"
        assert s1a2["scoped_id"] == "TestStruct1::a2"
        assert s1a2["scoped_displayname"] == "TestStruct1::a2"
        assert s1a2["type"] == "float"
        assert s1a2["scope"] is struct1

        s1a3 = summary["TestStruct1::a3"]
        assert type(s1a3).__name__ == "MemberObject"
        assert s1a3["id"] == "a3"
        assert s1a3["scoped_id"] == "TestStruct1::a3"
        assert s1a3["scoped_displayname"] == "TestStruct1::a3"
        assert s1a3["type"] == "bool"
        assert s1a3["scope"] is struct1

        struct2 = summary["TestStruct2"]
        assert type(struct2).__name__ == "ClassObject"
        assert struct2["id"] == "TestStruct2"
        assert struct2["scoped_id"] == "TestStruct2"
        assert struct2["scoped_displayname"] == "TestStruct2"

        s2a1 = summary["TestStruct2::a1"]
        assert type(s2a1).__name__ == "MemberObject"
        assert s2a1["id"] == "a1"
        assert s2a1["scoped_id"] == "TestStruct2::a1"
        assert s2a1["scoped_displayname"] == "TestStruct2::a1"
        assert s2a1["type"] == "std::string"
        assert s2a1["scope"] is struct2

        s2a2 = summary["TestStruct2::a2"]
        assert type(s2a2).__name__ == "MemberObject"
        assert s2a2["id"] == "a2"
        assert s2a2["scoped_id"] == "TestStruct2::a2"
        assert s2a2["scoped_displayname"] == "TestStruct2::a2"
        assert s2a2["type"] == "int"
        assert s2a2["scope"] is struct2

        s2a3 = summary["TestStruct2::a3"]
        assert type(s2a3).__name__ == "MemberObject"
        assert s2a3["id"] == "a3"
        assert s2a3["scoped_id"] == "TestStruct2::a3"
        assert s2a3["scoped_displayname"] == "TestStruct2::a3"
        assert s2a3["type"] == "std::map<std::string, int>"
        assert s2a3["scope"] is struct2

        s2ctor1 = summary["TestStruct2::TestStruct2()"]
        assert type(s2ctor1).__name__ == "MemberFunctionObject"
        assert s2ctor1["scoped_id"] == "TestStruct2::TestStruct2"
        assert s2ctor1["scoped_displayname"] == "TestStruct2::TestStruct2()"
        assert s2ctor1["displayname"] in struct2["constructors"]
        assert s2ctor1["scope"] is struct2

        s2ctor2 = summary["TestStruct2::TestStruct2(int)"]
        assert type(s2ctor2).__name__ == "MemberFunctionObject"
        assert s2ctor2["scoped_id"] == "TestStruct2::TestStruct2"
        assert s2ctor2["scoped_displayname"] == "TestStruct2::TestStruct2(int)"
        assert s2ctor2["displayname"] in struct2["constructors"]
        assert s2ctor2["displayname"] in struct2["conversion_functions"]
        assert s2ctor2["scope"] is struct2

        s2dtor1 = summary["TestStruct2::~TestStruct2()"]
        assert type(s2dtor1).__name__ == "MemberFunctionObject"
        assert s2dtor1["scoped_id"] == "TestStruct2::~TestStruct2"
        assert s2dtor1["scoped_displayname"] == "TestStruct2::~TestStruct2()"
        assert s2dtor1["displayname"] in struct2["destructors"]
        assert s2dtor1["scope"] is struct2

        s2m1 = summary["TestStruct2::testMethod1()"]
        assert type(s2m1).__name__ == "MemberFunctionObject"
        assert s2m1["scoped_id"] == "TestStruct2::testMethod1"
        assert s2m1["scoped_displayname"] == "TestStruct2::testMethod1()"
        assert s2m1["displayname"] in struct2["functions"]
        assert s2m1["return"] == "double"
        assert s2m1["scope"] is struct2

        s2m2 = summary["TestStruct2::testMethod2(std::string)"]
        assert type(s2m2).__name__ == "MemberFunctionObject"
        assert s2m2["scoped_id"] == "TestStruct2::testMethod2"
        assert s2m2["scoped_displayname"] == "TestStruct2::testMethod2(std::string)"
        assert s2m2["displayname"] in struct2["functions"]
        assert s2m2["return"] == "double"
        assert s2m2["params"]["param0"]["type"] == "std::string"
        assert s2m2["scope"] is struct2

        s2m3 = summary["TestStruct2::testMethod3(int)"]
        assert type(s2m3).__name__ == "MemberFunctionObject"
        assert s2m3["scoped_id"] == "TestStruct2::testMethod3"
        assert s2m3["scoped_displayname"] == "TestStruct2::testMethod3(int)"
        assert s2m3["displayname"] in struct2["functions"]
        assert s2m3["return"] == "void *"
        assert s2m3["params"]["param0"]["type"] == "int"
        assert s2m3["scope"] is struct2

        class1 = summary["TestClass1"]
        assert type(class1).__name__ == "ClassObject"
        assert class1["id"] == "TestClass1"
        assert class1["scoped_id"] == "TestClass1"
        assert class1["scoped_displayname"] == "TestClass1"

        c1ctor1 = summary["TestClass1::TestClass1()"]
        assert type(c1ctor1).__name__ == "MemberFunctionObject"
        assert c1ctor1["id"] == "TestClass1"
        assert c1ctor1["scoped_id"] == "TestClass1::TestClass1"
        assert c1ctor1["scoped_displayname"] == "TestClass1::TestClass1()"
        assert c1ctor1["displayname"] in class1["constructors"]
        assert c1ctor1["scope"] is class1

        c1ctor2 = summary["TestClass1::TestClass1(double)"]
        assert type(c1ctor2).__name__ == "MemberFunctionObject"
        assert c1ctor2["id"] == "TestClass1"
        assert c1ctor2["scoped_id"] == "TestClass1::TestClass1"
        assert c1ctor2["scoped_displayname"] == "TestClass1::TestClass1(double)"
        assert c1ctor2["displayname"] in class1["constructors"]
        assert c1ctor2["displayname"] in class1["conversion_functions"]
        assert c1ctor2["scope"] is class1

        c1dtor1 = summary["TestClass1::~TestClass1()"]
        assert type(c1dtor1).__name__ == "MemberFunctionObject"
        assert c1dtor1["id"] == "~TestClass1"
        assert c1dtor1["scoped_id"] == "TestClass1::~TestClass1"
        assert c1dtor1["scoped_displayname"] == "TestClass1::~TestClass1()"
        assert c1dtor1["displayname"] in class1["destructors"]
        assert c1dtor1["scope"] is class1

        c1u1 = summary["TestClass1::u1"]
        assert type(c1u1).__name__ == "MemberObject"
        assert c1u1["id"] == "u1"
        assert c1u1["scoped_id"] == "TestClass1::u1"
        assert c1u1["scoped_displayname"] == "TestClass1::u1"
        assert c1u1["displayname"] in class1["variables"]
        assert c1u1["type"] == "double"
        assert c1u1["scope"] is class1

        c1u2 = summary["TestClass1::u2"]
        assert type(c1u2).__name__ == "MemberObject"
        assert c1u2["id"] == "u2"
        assert c1u2["scoped_id"] == "TestClass1::u2"
        assert c1u2["scoped_displayname"] == "TestClass1::u2"
        assert c1u2["displayname"] in class1["variables"]
        assert c1u2["type"] == "float"
        assert c1u2["scope"] is class1

        c1e1 = summary["TestClass1::TEST_ENUM1"]
        assert type(c1e1).__name__ == "EnumConstDeclObject"
        assert c1e1["id"] == "TEST_ENUM1"
        assert c1e1["scoped_id"] == "TestClass1::TEST_ENUM1"
        assert c1e1["scoped_displayname"] == "TestClass1::TEST_ENUM1"
        assert c1e1["value"] == str(0)
        assert c1e1["displayname"] in class1["exported_constants"]
        assert c1e1["scope"] is class1

        c1e2 = summary["TestClass1::TEST_ENUM2"]
        assert type(c1e2).__name__ == "EnumConstDeclObject"
        assert c1e2["id"] == "TEST_ENUM2"
        assert c1e2["scoped_id"] == "TestClass1::TEST_ENUM2"
        assert c1e2["scoped_displayname"] == "TestClass1::TEST_ENUM2"
        assert c1e2["value"] == str(1)
        assert c1e2["displayname"] in class1["exported_constants"]
        assert c1e2["scope"] is class1

        tdef_type = summary["TestClass1::tdef_type"]
        assert type(tdef_type).__name__ == "ClassObject"
        assert tdef_type["id"] == "tdef_type"
        assert tdef_type["scoped_id"] == "TestClass1::tdef_type"
        assert tdef_type["scoped_displayname"] == "TestClass1::tdef_type"
        assert tdef_type["scope"] is class1

        tds1 = summary["TestClass1::tdef_type::s1"]
        assert type(tds1).__name__ == "MemberObject"
        assert tds1["id"] == "s1"
        assert tds1["scoped_id"] == "TestClass1::tdef_type::s1"
        assert tds1["scoped_displayname"] == "TestClass1::tdef_type::s1"
        assert tds1["type"] == "double"
        assert tds1["displayname"] in tdef_type["variables"]
        assert tds1["scope"] is tdef_type

        tds2 = summary["TestClass1::tdef_type::s2"]
        assert type(tds2).__name__ == "MemberObject"
        assert tds2["id"] == "s2"
        assert tds2["scoped_id"] == "TestClass1::tdef_type::s2"
        assert tds2["scoped_displayname"] == "TestClass1::tdef_type::s2"
        assert tds2["type"] == "float"
        assert tds2["displayname"] in tdef_type["variables"]
        assert tds2["scope"] is tdef_type

        nc1 = summary["TestClass1::NestedClass1"]
        assert type(nc1).__name__ == "ClassObject"
        assert nc1["id"] == "NestedClass1"
        assert nc1["scoped_id"] == "TestClass1::NestedClass1"
        assert nc1["scoped_displayname"] == "TestClass1::NestedClass1"
        assert nc1["scope"] is class1

        nc1ctor1 = summary["TestClass1::NestedClass1::NestedClass1()"]
        assert type(nc1ctor1).__name__ == "MemberFunctionObject"
        assert nc1ctor1["id"] == "NestedClass1"
        assert nc1ctor1["scoped_id"] == "TestClass1::NestedClass1::NestedClass1"
        assert (
            nc1ctor1["scoped_displayname"] == "TestClass1::NestedClass1::NestedClass1()"
        )
        assert nc1ctor1["displayname"] in nc1["constructors"]
        assert nc1ctor1["scope"] is nc1

        nc1dtor1 = summary["TestClass1::NestedClass1::~NestedClass1()"]
        assert type(nc1dtor1).__name__ == "MemberFunctionObject"
        assert nc1dtor1["id"] == "~NestedClass1"
        assert nc1dtor1["scoped_id"] == "TestClass1::NestedClass1::~NestedClass1"
        assert (
            nc1dtor1["scoped_displayname"]
            == "TestClass1::NestedClass1::~NestedClass1()"
        )
        assert nc1dtor1["displayname"] in nc1["destructors"]
        assert nc1dtor1["scope"] is nc1

        nc1n1 = summary["TestClass1::NestedClass1::n1"]
        assert type(nc1n1).__name__ == "MemberObject"
        assert nc1n1["id"] == "n1"
        assert nc1n1["scoped_id"] == "TestClass1::NestedClass1::n1"
        assert nc1n1["scoped_displayname"] == "TestClass1::NestedClass1::n1"
        assert nc1n1["type"] == "double"
        assert nc1n1["displayname"] in nc1["variables"]
        assert nc1n1["scope"] is nc1

        nc1m1 = summary["TestClass1::NestedClass1::testMethod1()"]
        assert type(nc1m1).__name__ == "MemberFunctionObject"
        assert nc1m1["id"] == "testMethod1"
        assert nc1m1["scoped_id"] == "TestClass1::NestedClass1::testMethod1"
        assert nc1m1["scoped_displayname"] == "TestClass1::NestedClass1::testMethod1()"
        assert nc1m1["return"] == "void"
        assert nc1m1["displayname"] in nc1["functions"]
        assert nc1m1["scope"] is nc1

        c1b1 = summary["TestClass1::b1"]
        assert type(c1b1).__name__ == "MemberObject"
        assert c1b1["id"] == "b1"
        assert c1b1["scoped_id"] == "TestClass1::b1"
        assert c1b1["scoped_displayname"] == "TestClass1::b1"
        assert c1b1["type"] == "std::string"
        assert c1b1["displayname"] in class1["variables"]
        assert c1b1["scope"] is class1

        c1b2 = summary["TestClass1::b2"]
        assert type(c1b2).__name__ == "MemberObject"
        assert c1b2["id"] == "b2"
        assert c1b2["scoped_id"] == "TestClass1::b2"
        assert c1b2["scoped_displayname"] == "TestClass1::b2"
        assert c1b2["type"] == "std::vector<double>"
        assert c1b2["displayname"] in class1["variables"]
        assert c1b2["scope"] is class1

        c1b3 = summary["TestClass1::b3"]
        assert type(c1b3).__name__ == "MemberObject"
        assert c1b3["id"] == "b3"
        assert c1b3["scoped_id"] == "TestClass1::b3"
        assert c1b3["scoped_displayname"] == "TestClass1::b3"
        assert c1b3["type"] == "std::array<double, 3>"
        assert c1b3["displayname"] in class1["variables"]
        assert c1b3["scope"] is class1

        c1m4 = summary["TestClass1::testMethod4()"]
        assert type(c1m4).__name__ == "MemberFunctionObject"
        assert c1m4["id"] == "testMethod4"
        assert c1m4["scoped_id"] == "TestClass1::testMethod4"
        assert c1m4["scoped_displayname"] == "TestClass1::testMethod4()"
        assert c1m4["return"] == "void"
        assert c1m4["displayname"] in class1["functions"]
        assert c1m4["scope"] is class1

        c1t1 = summary["TestClass1::t1"]
        assert type(c1t1).__name__ == "MemberObject"
        assert c1t1["id"] == "t1"
        assert c1t1["scoped_id"] == "TestClass1::t1"
        assert c1t1["scoped_displayname"] == "TestClass1::t1"
        assert c1t1["type"] == "double"
        assert c1t1["displayname"] in class1["variables"]
        assert c1t1["access_specifier"] == "PRIVATE"
        assert c1t1["scope"] is class1

        c1t2 = summary["TestClass1::t2"]
        assert type(c1t2).__name__ == "MemberObject"
        assert c1t2["id"] == "t2"
        assert c1t2["scoped_id"] == "TestClass1::t2"
        assert c1t2["scoped_displayname"] == "TestClass1::t2"
        assert c1t2["type"] == "float"
        assert c1t2["displayname"] in class1["variables"]
        assert c1t2["access_specifier"] == "PRIVATE"
        assert c1t2["scope"] is class1

        c1m5 = summary["TestClass1::testMethod5(std::string, std::vector<double> &)"]
        assert type(c1m5).__name__ == "MemberFunctionObject"
        assert c1m5["id"] == "testMethod5"
        assert c1m5["scoped_id"] == "TestClass1::testMethod5"
        assert (
            c1m5["scoped_displayname"]
            == "TestClass1::testMethod5(std::string, std::vector<double> &)"
        )
        assert c1m5["return"] == "float"
        assert c1m5["access_specifier"] == "PRIVATE"
        assert c1m5["scope"] is class1

        class2 = summary["TestClass2"]
        assert type(class2).__name__ == "ClassObject"
        assert class2["id"] == "TestClass2"
        assert class2["scoped_id"] == "TestClass2"
        assert class2["scoped_displayname"] == "TestClass2"

        c2ctor1 = summary["TestClass2::TestClass2()"]
        assert type(c2ctor1).__name__ == "MemberFunctionObject"
        assert c2ctor1["id"] == "TestClass2"
        assert c2ctor1["scoped_id"] == "TestClass2::TestClass2"
        assert c2ctor1["scoped_displayname"] == "TestClass2::TestClass2()"
        assert c2ctor1["displayname"] in class2["constructors"]
        assert c2ctor1["scope"] is class2

        c2dtor1 = summary["TestClass2::~TestClass2()"]
        assert type(c2dtor1).__name__ == "MemberFunctionObject"
        assert c2dtor1["id"] == "~TestClass2"
        assert c2dtor1["scoped_id"] == "TestClass2::~TestClass2"
        assert c2dtor1["scoped_displayname"] == "TestClass2::~TestClass2()"
        assert c2dtor1["displayname"] in class2["destructors"]
        assert c2dtor1["scope"] is class2

        c2base1 = class2["base_classes"]["TestStruct2"]
        assert c2base1["base_class"] is struct2
        assert c2base1["access_specifier"] == "PUBLIC"

        c2base2 = class2["base_classes"]["TestClass1"]
        assert c2base2["base_class"] is class1
        assert c2base2["access_specifier"] == "PRIVATE"

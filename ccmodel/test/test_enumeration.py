import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_enumeration
class TestCCModelEnum(CCModelTest):
    parse_state = ParseHeader("enumeration_test.hh", "enumeration_test", [])

    def test_parse_object_exsts(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        pdb.set_trace()
        expected = [
            "testEnum1",
            "A",
            "B",
            "testEnum2",
            "testEnum2::A",
            "testEnum2::B",
            "testEnum2::C",
            "Nest1",
            "Nest1::testEnum3",
            "Nest1::A1",
            "Nest1::A2",
            "Nest1::A3",
            "Nest1::A4",
            "Nest1::testEnum4",
            "Nest1::testEnum4::A",
            "Nest1::testEnum4::B",
            "Nest1::testEnum4::C",
        ]
        for exp in expected:
            assert summary.name_in_summary(exp)

        return

    def test_enumeration_data(cls_type, lps):
        summary = lps[cls_type.parse_state.test_file_abs]

        enum1 = summary["testEnum1"]
        assert enum1["inherits_from"] == "unsigned int"
        assert enum1["is_scoped"] == False
        assert enum1["id"] == "testEnum1"
        assert enum1["scoped_id"] == "testEnum1"
        assert enum1["scoped_displayname"] == "testEnum1"

        assert enum1["fields"]["A"]["value"] == str(0)
        assert enum1["fields"]["A"] is summary["A"]

        assert enum1["fields"]["B"]["value"] == str(1)
        assert enum1["fields"]["B"] is summary["B"]

        assert enum1["fields"]["A"]["id"] == "A"
        assert enum1["fields"]["A"]["scoped_id"] == "A"
        assert enum1["fields"]["A"]["scoped_displayname"] == "A"

        assert enum1["fields"]["B"]["id"] == "B"
        assert enum1["fields"]["B"]["scoped_id"] == "B"
        assert enum1["fields"]["B"]["scoped_displayname"] == "B"

        enum2 = summary["testEnum2"]
        assert enum2["inherits_from"] == "int"
        assert enum2["is_scoped"] == True
        assert enum2["id"] == "testEnum2"
        assert enum2["scoped_id"] == "testEnum2"
        assert enum2["scoped_displayname"] == "testEnum2"

        pdb.set_trace()
        assert enum2["fields"]["A"]["value"] == str(0)
        assert enum2["fields"]["A"] is summary["testEnum2::A"]

        assert enum2["fields"]["B"]["value"] == str(1)
        assert enum2["fields"]["B"] is summary["testEnum2::B"]

        assert enum2["fields"]["C"]["value"] == str(2)
        assert enum2["fields"]["C"] is summary["testEnum2::C"]

        assert enum2["fields"]["A"]["id"] == "A"
        assert enum2["fields"]["A"]["scoped_id"] == "testEnum2::A"
        assert enum2["fields"]["A"]["scoped_displayname"] == "testEnum2::A"

        assert enum2["fields"]["B"]["id"] == "B"
        assert enum2["fields"]["B"]["scoped_id"] == "testEnum2::B"
        assert enum2["fields"]["B"]["scoped_displayname"] == "testEnum2::B"

        assert enum2["fields"]["C"]["id"] == "C"
        assert enum2["fields"]["C"]["scoped_id"] == "testEnum2::C"
        assert enum2["fields"]["C"]["scoped_displayname"] == "testEnum2::C"

        enum3 = summary["Nest1::testEnum3"]
        assert enum3["inherits_from"] == "unsigned int"
        assert enum3["is_scoped"] == False
        assert enum3["id"] == "testEnum3"
        assert enum3["scoped_id"] == "Nest1::testEnum3"
        assert enum3["scoped_displayname"] == "Nest1::testEnum3"

        assert enum3["fields"]["A1"]["value"] == str(0)
        assert enum3["fields"]["A1"] is summary["Nest1::A1"]

        assert enum3["fields"]["A2"]["value"] == str(1)
        assert enum3["fields"]["A2"] is summary["Nest1::A2"]

        assert enum3["fields"]["A3"]["value"] == str(2)
        assert enum3["fields"]["A3"] is summary["Nest1::A3"]

        assert enum3["fields"]["A4"]["value"] == str(4)
        assert enum3["fields"]["A4"] is summary["Nest1::A4"]

        assert enum3["fields"]["A1"]["id"] == "A1"
        assert enum3["fields"]["A1"]["scoped_id"] == "Nest1::A1"
        assert enum3["fields"]["A1"]["scoped_displayname"] == "Nest1::A1"

        assert enum3["fields"]["A2"]["id"] == "A2"
        assert enum3["fields"]["A2"]["scoped_id"] == "Nest1::A2"
        assert enum3["fields"]["A2"]["scoped_displayname"] == "Nest1::A2"

        assert enum3["fields"]["A3"]["id"] == "A3"
        assert enum3["fields"]["A3"]["scoped_id"] == "Nest1::A3"
        assert enum3["fields"]["A3"]["scoped_displayname"] == "Nest1::A3"

        assert enum3["fields"]["A4"]["id"] == "A4"
        assert enum3["fields"]["A4"]["scoped_id"] == "Nest1::A4"
        assert enum3["fields"]["A4"]["scoped_displayname"] == "Nest1::A4"

        enum4 = summary["Nest1::testEnum4"]
        assert enum4["inherits_from"] == "int32_t"
        assert enum4["is_scoped"] == True
        assert enum4["id"] == "testEnum4"
        assert enum4["scoped_id"] == "Nest1::testEnum4"
        assert enum4["scoped_displayname"] == "Nest1::testEnum4"

        assert enum4["fields"]["A"]["value"] == str(0)
        assert enum4["fields"]["A"] is summary["Nest1::testEnum4::A"]

        assert enum4["fields"]["B"]["value"] == str(1)
        assert enum4["fields"]["B"] is summary["Nest1::testEnum4::B"]

        assert enum4["fields"]["C"]["value"] == str(2)
        assert enum4["fields"]["C"] is summary["Nest1::testEnum4::C"]

        assert enum4["fields"]["A"]["id"] == "A"
        assert enum4["fields"]["A"]["scoped_id"] == "Nest1::testEnum4::A"
        assert enum4["fields"]["A"]["scoped_displayname"] == "Nest1::testEnum4::A"

        assert enum4["fields"]["B"]["id"] == "B"
        assert enum4["fields"]["B"]["scoped_id"] == "Nest1::testEnum4::B"
        assert enum4["fields"]["B"]["scoped_displayname"] == "Nest1::testEnum4::B"

        assert enum4["fields"]["C"]["id"] == "C"
        assert enum4["fields"]["C"]["scoped_id"] == "Nest1::testEnum4::C"
        assert enum4["fields"]["C"]["scoped_displayname"] == "Nest1::testEnum4::C"

        return

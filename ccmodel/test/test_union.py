import pytest
import os
import pdb

from typing import Dict
from .common import ParseHeader, CCModelTest


@pytest.mark.test_union
class TestCCModelUnion(CCModelTest):
    parse_state = ParseHeader("union_test.hh", "union_test", [])

    def test_parse_objects_exist(cls_type, lps):
        summary = lps

        expected = [
            "testUnion1",
            "testUnion1::s1",
            "testUnion1::s2",
            "testUnion1::s3",
            "testUnion1::s4",
            "Nest1::Nest2::s1",
            "Nest1::Nest2::s2",
            "Nest1::Nest2::s3",
            "Nest1::Nest2::s4",
        ]
        for exp in expected:
            assert summary.name_in_summary(exp)

    def test_unions(cls_type, lps):
        summary = lps

        union1 = summary["testUnion1"]
        assert union1["id"] == "testUnion1"
        assert union1["scoped_id"] == "testUnion1"
        assert union1["scoped_displayname"] == "testUnion1"

        u1s1 = summary["testUnion1::s1"]
        assert u1s1["scope"] == union1
        assert u1s1["id"] == "s1"
        assert u1s1["scoped_id"] == "testUnion1::s1"
        assert u1s1["scoped_displayname"] == "testUnion1::s1"
        assert u1s1["type"] == "double"

        u1s2 = summary["testUnion1::s2"]
        assert u1s2["scope"] == union1
        assert u1s2["id"] == "s2"
        assert u1s2["scoped_id"] == "testUnion1::s2"
        assert u1s2["scoped_displayname"] == "testUnion1::s2"
        assert u1s2["type"] == "float"

        u1s3 = summary["testUnion1::s3"]
        assert u1s3["scope"] == union1
        assert u1s3["id"] == "s3"
        assert u1s3["scoped_id"] == "testUnion1::s3"
        assert u1s3["scoped_displayname"] == "testUnion1::s3"
        assert u1s3["type"] == "int"

        u1s4 = summary["testUnion1::s4"]
        assert u1s4["scope"] == union1
        assert u1s4["id"] == "s4"
        assert u1s4["scoped_id"] == "testUnion1::s4"
        assert u1s4["scoped_displayname"] == "testUnion1::s4"
        assert u1s4["type"] == "bool"

        nest2 = summary["Nest1::Nest2"]

        u2s1 = summary["Nest1::Nest2::s1"]
        assert u2s1["scope"] == nest2
        assert u2s1["id"] == "s1"
        assert u2s1["scoped_id"] == "Nest1::Nest2::s1"
        assert u2s1["scoped_displayname"] == "Nest1::Nest2::s1"
        assert u2s1["type"] == "double"

        u2s2 = summary["Nest1::Nest2::s2"]
        assert u2s2["scope"] == nest2
        assert u2s2["id"] == "s2"
        assert u2s2["scoped_id"] == "Nest1::Nest2::s2"
        assert u2s2["scoped_displayname"] == "Nest1::Nest2::s2"
        assert u2s2["type"] == "float"

        u2s3 = summary["Nest1::Nest2::s3"]
        assert u2s3["scope"] == nest2
        assert u2s3["id"] == "s3"
        assert u2s3["scoped_id"] == "Nest1::Nest2::s3"
        assert u2s3["scoped_displayname"] == "Nest1::Nest2::s3"
        assert u2s3["type"] == "int"

        u2s4 = summary["Nest1::Nest2::s4"]
        assert u2s4["scope"] == nest2
        assert u2s4["id"] == "s4"
        assert u2s4["scoped_id"] == "Nest1::Nest2::s4"
        assert u2s4["scoped_displayname"] == "Nest1::Nest2::s4"
        assert u2s4["type"] == "bool"

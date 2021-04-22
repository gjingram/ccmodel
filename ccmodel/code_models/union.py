from clang import cindex, enumerations
import typing
import pdb

from .decorators import (if_handle, 
        append_cpo)
from .parse_object import ParseObject
from .class_object import ClassObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.UNION_DECL)
class UnionObject(ClassObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ClassObject.__init__(self, node, force)
        self["is_union"] = True
        if node is not None:
            self.determine_scope_name(node)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'UnionObject':
        ParseObject.handle(self, node)

        sid = self["id"]
        scoped_id = self["scoped_id"]
        scoped_displayname = self["scoped_displayname"]
        if self["export_to_scope"]:
            self["id"] = ""
            self["scoped_id"] = ""
            self["scoped_displayname"] = ""
            self["scope"].handle(node)
        else:
            ClassObject.handle(self, node)
        self["id"] = sid
        self["scoped_id"] = scoped_id
        self["scoped_displayname"] = scoped_displayname

        self["header"].header_add_union(self)
        return self

from clang import cindex, enumerations
import typing
import pdb

from .decorators import (if_handle, 
        append_cpo)
from .parse_object import ParseObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.ENUM_CONSTANT_DECL)
class EnumConstDeclObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info["value"] = str(node.enum_value) if node is not None else ""
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'EnumConstDeclObject':
        self.determine_scope_name(node)
        return ParseObject.handle(self, node)

@cmm.default_code_model(cindex.CursorKind.ENUM_DECL)
class EnumObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info["inherits_from"] = node.enum_type.spelling
        self.info["is_scoped"] = node.is_scoped_enum()
        self.info["fields"] = {}
        self["export_to_scope"] = not self["is_scoped"]
        node.export_to_scope = self["export_to_scope"]
        self.determine_scope_name(node)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'EnumObject':
        ParseObject.handle(self, node)
        children = []
        self.extend_children(node, children)

        sid = self["id"]
        scoped_id = self["scoped_id"]
        scoped_displayname = self["scoped_displayname"]
        if self["export_to_scope"]:
            self["id"] = ""
            self["scoped_id"] = ""
            self["scoped_displayname"] = ""
        for child in self.children(children, node.kind.ENUM_CONSTANT_DECL):
            self.add_enum_field(self.create_clang_child_object(child)) 
        self["id"]= sid
        self["scoped_id"] = scoped_id
        self["scoped_displayname"] = scoped_displayname
        return self

    def add_enum_field(self, obj: 'EnumConstDeclObject') -> None:
        if obj is None:
            return
        if self["export_to_scope"] and self["scope"] is not None:
            self["scope"].add_exported_const(obj)
        self["fields"][obj["id"]] = obj
        return

    def create_clang_child_object(self, node: cindex.Cursor) -> 'EnumConstDeclObject':
        cpo_class = self.get_child_type(node)
        tparents = [*self["template_parents"], self] if self["is_template"] else \
                self["template_parents"]
        if self["is_scoped"]:
            return cpo_class(node).add_template_parents(tparents).set_header(self["header"])\
                    .set_scope(self).handle(node)
        return cpo_class(node).add_template_parents(tparents)\
                .set_header(self["header"]).set_scope(self["scope"]).handle(node)




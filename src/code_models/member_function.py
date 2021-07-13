from clang import cindex, enumerations
import typing
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .function import FunctionObject
from .types import class_type
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CONSTRUCTOR)
@cmm.default_code_model(cindex.CursorKind.DESTRUCTOR)
@cmm.default_code_model(cindex.CursorKind.CXX_METHOD)
@cmm.default_code_model(cindex.CursorKind.CONVERSION_FUNCTION)
class MemberFunctionObject(FunctionObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        FunctionObject.__init__(self, node, force)

        self.info["access_specifier"] = (
            node.access_specifier.name if node is not None else ""
        )
        self.info["is_const"] = node.is_const_method() if node is not None else False
        self.info["is_ctor"] = False
        self.info["is_dtor"] = False
        self.info["is_conversion"] = False
        self.info["is_converting_ctor"] = (
            node.is_converting_constructor() if node is not None else False
        )
        self.info["is_pure_virtual"] = (
            node.is_pure_virtual_method() if node is not None else False
        )
        self.info["is_virtual"] = (
            node.is_virtual_method() if node is not None else False
        )
        self.info["is_static"] = node.is_static_method() if node is not None else False
        self.info["is_final"] = False
        self.info["is_override"] = False
        if node is not None:
            self.determine_scope_name(node)
        self["displayname"] = (
            (self["displayname"] + " const")
            if self["is_const"]
            else self["displayname"]
        )
        self["scoped_displayname"] = (
            (self["scoped_displayname"] + " const")
            if self["is_const"]
            else self["scoped_displayname"]
        )

        return

    def update_class_type(self, scope: "ClassObject") -> None:
        if self["is_pure_virtual"]:
            scope.set_class_type(class_type["ABSTRACT"])
        elif self["is_virtual"]:
            scope.set_class_type(class_type["VIRTUAL"])
        else:
            scope.set_class_type(class_type["CONCRETE"])
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "MemberFunctionObject":

        self["is_member"] = True
        FunctionObject.handle(self, node)

        if self["is_ctor"] or self["is_dtor"]:
            self["id"] = self["scope"]["id"]
            self["displayname"] = (
                self["scope"]["displayname"]
                + "("
                + f"{', '.join([x['type'] for x in self['params'].values()])}"
                + ")"
            )
            if self["is_dtor"]:
                self["id"] = "~" + self["id"]
                self["displayname"] = "~" + self["displayname"]
            
        
        self["scoped_id"] = "::".join([self["scope"]["scoped_id"], self["id"]])
        self["scoped_displayname"] = "::".join(
                [self["scope"]["scoped_displayname"], self["displayname"]])

        if not self["is_template"]:
            ParseObject.handle(self, node)

        children = []
        self.extend_children(node, children)

        self.update_class_type(self["scope"])

        for child in children:
            if child.kind == cindex.CursorKind.CXX_FINAL_ATTR and not self["is_final"]:
                self["is_final"] = True
            if (
                child.kind == cindex.CursorKind.CXX_OVERRIDE_ATTR
                and not self["is_override"]
            ):
                self["is_override"] = True

        return self

    def mark_ctor(self, is_it: bool) -> "MemberFunctionObject":
        self["is_ctor"] = is_it
        return self

    def mark_dtor(self, is_it: bool) -> "MemberFunctionObject":
        self["is_dtor"] = is_it
        return self

    def mark_conversion(self, is_it: bool) -> "MemberFunctionObject":
        self["is_conversion"] = is_it
        return self

from clang import cindex, enumerations
import typing
import abc
import re
import copy
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .template import TemplateObject
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser


class AliasObject(ParseObject, metaclass=abc.ABCMeta):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force_parse: bool = False):
        ParseObject.__init__(self, node, force_parse)

        self.info["alias_name"] = ""
        self.info["aliased_name"] = ""
        self.info["aliased_usr"] = ""
        self.info["aliased_object"] = None
        self["is_alias"] = True
        if node is not None:
            self.determine_scope_name(node)

        return

    @abc.abstractmethod
    def handle(self, node: cindex.Cursor) -> "AliasObject":
        return


@cmm.default_code_model(cindex.CursorKind.TYPEDEF_DECL)
class TypeDefObject(AliasObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        AliasObject.__init__(self, node, force)
        self.info["type_aliased"] = ""
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "TypeDefObject":
        children = []
        self.extend_children(node, children)

        structs_and_classes = self.children(children, cindex.CursorKind.STRUCT_DECL)
        structs_and_classes.extend(
            self.children(children, cindex.CursorKind.CLASS_DECL)
        )

        for child in structs_and_classes:
            header_use = parser.get_header(child.location.file.name)
            model = cmm.default_code_models[child.kind]
            obj = None
            pdb.set_trace()
            if child.spelling == "":
                obj = (
                    model(child, force=True, name=self.get_name())
                    .add_template_parents(self["template_parents"])
                    .set_header(header_use)
                    .set_scope(self["scope"])
                    .add_active_namespaces(self.active_namespaces)
                    .add_active_directives(self.active_using_directives)
                    .set_parse_level(self["parse_level"])
                    .do_handle(child)
                    .handle(child)
                )
            else:
                obj = (
                    model(child, force=True)
                    .add_template_parents(self["template_parents"])
                    .set_header(header_use)
                    .set_scope(self["scope"])
                    .add_active_namespaces(self.active_namespaces)
                    .add_active_directives(self.active_using_directives)
                    .set_parse_level(self["parse_level"])
                    .do_handle(child)
                    .handle(child)
                )
            # self["header"].header_add_fns[child.kind.name](obj)
            # self["header"].summary.identifier_map[obj["scoped_displayname"]] = obj["usr"]
            # self["header"].summary.usr_map[obj["usr"]] = obj

            if child.spelling == "":
                return None
        
        self.resolve_alias(node)
        ParseObject.handle(self, node)
        return self

    def resolve_alias(self, node: cindex.Cursor) -> None:
        underlying_decl = node.underlying_typedef_type.get_declaration()
        if not underlying_decl.kind == cindex.CursorKind.NO_DECL_FOUND:
            recursion_detected = False
            parent = self["scope"]
            while parent and parent["id"] != "GlobalNamespace":
                if underlying_decl.spelling == parent["id"]:
                    recursion_detected = True
                    break
                parent = parent["scope"]
            if recursion_detected:
                self["type_aliased"] = parent
            else:
                self["type_aliased"] = self["header"].header_get_dep(
                    underlying_decl, self
                )
            if self["type_aliased"] is None:
                self["type_aliased"] = underlying_decl.spelling
            self["alias_name"] = self["scoped_displayname"]
            if type(self["type_aliased"]) is str:
                self["aliased_name"] = self["type_aliased"]
                self["aliased_usr"] = self["type_aliased"]
            else:
                self["aliased_name"] = self["type_aliased"]["scoped_displayname"]
                self["aliased_usr"] = self["type_aliased"]["usr"]
        else:
            self["type_aliased"] = node.underlying_typedef_type.spelling
            self["alias_name"] = self["scoped_displayname"]
            self["aliased_name"] = node.underlying_typedef_type.spelling
            self["aliased_usr"] = node.underlying_typedef_type.spelling
        self["aliased_object"] = self["type_aliased"]
        return


@cmm.default_code_model(cindex.CursorKind.TYPE_ALIAS_DECL)
class TypeAliasObject(TypeDefObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        TypeDefObject.__init__(self, node, force)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "TypeAliasObject":
        return TypeDefObject.handle(self, node)


@cmm.default_code_model(cindex.CursorKind.NAMESPACE_ALIAS)
class NamespaceAliasObject(AliasObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        AliasObject.__init__(self, node, force)
        self.info["namespace_aliased"] = ""
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "NamespaceAliasObject":
        children = []
        self.extend_children(node, children)

        for child in self.children(children, cindex.CursorKind.NAMESPACE_REF):
            self["aliased_name"] = (
                child.spelling
                if self["aliased_name"] == ""
                else self["aliased_name"] + "::" + child.spelling
            )

        child = self.children(children, cindex.CursorKind.NAMESPACE_REF)[-1]
        self.info["namespace_aliased"] = self["header"].header_get_dep(child, self)
        self.info["alias_name"] = self["scoped_displayname"]

        ParseObject.handle(self, node)
        return self


@cmm.default_code_model(cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL)
class TemplateAliasObject(TypeAliasObject, TemplateObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        TypeAliasObject.__init__(self, node, force)
        TemplateObject.__init__(self, node, force)
        self["is_alias"] = True
        self.info["template_ref"] = None
        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> "TemplateAliasObject":

        self.resolve_alias(node)
        TemplateObject.handle(self, node)

        return self

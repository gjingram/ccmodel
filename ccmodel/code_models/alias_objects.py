from clang import cindex, enumerations
import typing
import abc
import re
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject, replace_template_params
from .template import PartialSpecializationObject
from ..rules import code_model_map as cmm


class AliasObject(ParseObject, metaclass=abc.ABCMeta):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.alias = ""
        self.original_cpp_object = False
        self.alias_object = None

        self.determine_scope_name(node)

        return

    @abc.abstractmethod
    def handle(self, node: cindex.Cursor) -> 'AliasObject':
        pass

    def get_alias(self) -> str:
        return self.alias

    def get_using_string(self) -> str:
        return "using " + self.scoped_id + " = " + self.alias + ";"


@cmm.default_code_model(cindex.CursorKind.TYPEDEF_DECL)
class TypeDefObject(AliasObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        AliasObject.__init__(self, node, force)
        alias_tmp = node.underlying_typedef_type.spelling
        
        self.alias = node.underlying_typedef_type.spelling

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'TypeDefObject':
        for child in self.children(node, cindex.CursorKind.STRUCT_DECL):
            model = cmm.default_code_models[child.kind]
            obj = model(child, force=True, name=self.get_name()).add_template_parents(self.template_parents)\
                    .set_header(self.header)\
                    .set_scope(self.scope).handle(child)
            self.header.header_add_fns[child.kind](obj)
            self.header.summary.identifier_map[obj.scoped_displayname] = obj.usr
            self.header.summary.usr_map[obj.usr] = obj
            return None

        ParseObject.handle(self, node)
        for child in node.get_children():
            if child.kind != cindex.CursorKind.NAMESPACE_REF:
                self.header.header_get_dep(child, self)

        self.header.header_add_typedef(self)
        return self


@cmm.default_code_model(cindex.CursorKind.TYPE_ALIAS_DECL)
class TypeAliasObject(TypeDefObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        TypeDefObject.__init__(self, node, force)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'TypeAliasObject':
        return TypeDefObject.handle(self, node)


@cmm.default_code_model(cindex.CursorKind.NAMESPACE_ALIAS)
class NamespaceAliasObject(AliasObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        AliasObject.__init__(self, node, force)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'NamespaceAliasObject':

        ParseObject.handle(self, node)
        
        for child in self.children(node, cindex.CursorKind.NAMESPACE_REF):
            self.alias = child.spelling if self.alias == "" else self.alias + "::" + child.spelling

        child = self.children(node, cindex.CursorKind.NAMESPACE_REF)[-1]
        self.header.header_get_dep(child, self)

        return self


@cmm.default_code_model(cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL)
class TemplateAliasObject(TypeAliasObject, PartialSpecializationObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        TypeAliasObject.__init__(self, node, force)
        PartialSpecializationObject.__init__(self, node, force)
        self.is_alias = True
        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TemplateAliasObject':

        replace_template_params(self)
        PartialSpecializationObject.handle(self, node)

        return self

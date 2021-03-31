from clang import cindex, enumerations
import typing
import abc
import re
import pdb

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
from illuminate.code_models.template import TemplateObject
from illuminate.collections.unit_summary import UnitSummary
import illuminate.rules.code_model_map as cmm


class AliasObject(ParseObject, metaclass=abc.ABCMeta):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.alias = ""
        self.original_cpp_object = False
        self.alias_object = None

        return

    @abc.abstractmethod
    def handle(self, node: cindex.Cursor) -> 'AliasObject':
        pass

    def get_alias(self) -> str:
        return self.alias

    def get_using_string(self) -> str:
        return "using " + self.qualified_id + " = " + self.alias + ";"


@cmm.default_code_model(cindex.CursorKind.TYPEDEF_DECL)
class TypeDefObject(AliasObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        AliasObject.__init__(self, node, force)
        alias_tmp = node.underlying_typedef_type.spelling
        
        self.alias = node.underlying_typedef_type.spelling

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TypeDefObject':

        ParseObject.handle(self, node)

        for child in self.children(node, cindex.CursorKind.STRUCT_DECL):
            out = self.header.header_add_object(child)
            out.set_scope(self.scope)
            return None

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
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TypeAliasObject':
        return TypeDefObject.handle(self, node)


@cmm.default_code_model(cindex.CursorKind.NAMESPACE_ALIAS)
class NamespaceAliasObject(AliasObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        AliasObject.__init__(self, node, force)
        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'NamespaceAliasObject':

        ParseObject.handle(self, node)
        
        for child in self.children(node, cindex.CursorKind.NAMESPACE_REF):
            self.alias = child.spelling if self.alias == "" else self.alias + "::" + child.spelling

        child = self.children(node, cindex.CursorKind.NAMESPACE_REF)[-1]
        self.header.header_get_dep(child, self)

        return self


@cmm.default_code_model(cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL)
class TemplateAliasObject(AliasObject, TemplateObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        AliasObject.__init__(self, node, force)
        TemplateObject.__init__(self, node, force)

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TemplateAliasObject':

        TemplateObject.handle(self, node)

        tref = self.find_template_ref_node(node)
        self.header.header_get_dep(tref, self)

        return self

    def find_template_ref_node(self, node: cindex.Cursor) -> typing.Optional[cindex.Cursor]:
        children = [x for x in node.get_children()]
        result = None
        pdb.set_trace()
        for child in children:
            if child.kind == cindex.CursorKind.TEMPLATE_REF:
                result = child
                break
            else:
                result = self.find_template_ref_node(child)
                if result is not None and result.kind == cindex.CursorKind.TEMPLATE_REF:
                    break
        return result



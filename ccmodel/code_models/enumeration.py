from clang import cindex, enumerations
import typing
import pdb

from illuminate.code_models.decorators import (if_handle, 
        append_cpo)
from illuminate.code_models.parse_object import ParseObject
import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.ENUM_CONSTANT_DECL)
class EnumConstDeclObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.value = node.enum_value

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'EnumConstDeclObject':
        return ParseObject.handle(self, node)

@cmm.default_code_model(cindex.CursorKind.ENUM_DECL)
class EnumObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        
        self.inherits_from = node.enum_type.spelling  # Not considered an object dependency -- "type" dependency
        self.is_scoped = node.is_scoped_enum()
        self.fields = {}

        self.original_cpp_object = True

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'EnumObject':

        ParseObject.handle(self, node)

        for child in node.get_children():
            if child.kind == cindex.CursorKind.ENUM_CONSTANT_DECL:
                self.add_enum_field(self.create_clang_child_object(child)) 

        self.header.header_add_enum(self)
        return self

    def add_enum_field(self, obj: 'EnumConstDeclObject') -> None:
        self.fields[obj.id] = obj.value
        return

    def get_parent_class(self) -> str:
        return self.inherits_from

    def get_enum_scoped(self) -> bool:
        return self.is_scoped

    def create_clang_child_object(self, node: cindex.Cursor) -> 'EnumConstDeclObject':
        cpo_class = self.get_child_type(node)
        if self.is_scoped:
            return cpo_class(node).set_header(self.header).set_scope(self).handle(node)
        return cpo_class(node).set_header(self.header).set_scope(self.scope).handle(node)




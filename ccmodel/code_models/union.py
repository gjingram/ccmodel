from clang import cindex, enumerations
import typing

from illuminate.code_models.decorators import (if_handle, 
        append_cpo)
from illuminate.code_models.parse_object import ParseObject
import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.UNION_DECL)
class UnionObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.union_fields = {}
        self.original_cpp_object = True
        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'UnionObject':

        ParseObject.handle(self, node)

        for child in self.children(node, cindex.CursorKind.FIELD_DECL):
            self.add_union_field(self.create_clang_child_object(child))

        self.header.header_add_union(self)
        return self

    def add_union_field(self, field: 'MemberObject') -> None:
        self.union_fields[field.qualified_id] = field
        return

    def create_clang_child_object(self, node: cindex.Cursor) -> ParseObject:
        cpo_class = self.get_child_type(node)
        return cpo_class(node, self.force_parse).set_header(self.header).set_scope(self).handle(node)

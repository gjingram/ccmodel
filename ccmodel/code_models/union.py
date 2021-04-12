from clang import cindex, enumerations
import typing

from .decorators import (if_handle, 
        append_cpo)
from .parse_object import ParseObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.UNION_DECL)
class UnionObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.union_fields = {}
        self.original_cpp_object = True
        self.determine_scope_name(node)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'UnionObject':

        ParseObject.handle(self, node)

        for child in self.children(node, cindex.CursorKind.FIELD_DECL):
            self.add_union_field(self.create_clang_child_object(child))

        self.header.header_add_union(self)
        return self

    def add_union_field(self, field: 'MemberObject') -> None:
        self.union_fields[field.scoped_id] = field
        return

    def create_clang_child_object(self, node: cindex.Cursor) -> 'ParseObject':
        cpo_class = self.get_child_type(node)
        tparents = self.template_parents if not self.is_template else [*self.template_parents,
                self.template_ref]
        return cpo_class(node, self.force_parse).add_template_parents(tparents)\
                .set_header(self.header).set_scope(self).handle(node)

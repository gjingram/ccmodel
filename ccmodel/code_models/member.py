from clang import cindex, enumerations
import typing

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
from illuminate.code_models.variable import VariableObject

import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.FIELD_DECL)
class MemberObject(VariableObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        VariableObject.__init__(self, node, force)
        
        self.access_specifier = node.access_specifier
        self.original_cpp_object = True
        

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'MemberObject':
        is_member = True
        VariableObject.handle(self, node)
        return self

    def get_access_specifier(self) -> cindex.AccessSpecifier:
        return self.access_specifier

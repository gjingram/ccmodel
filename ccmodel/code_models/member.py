from clang import cindex, enumerations
import typing

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .variable import VariableObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.FIELD_DECL)
class MemberObject(VariableObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        VariableObject.__init__(self, node, force)
        
        self.access_specifier = node.access_specifier
        self.original_cpp_object = True
        

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'MemberObject':
        is_member = True
        VariableObject.handle(self, node)
        return self

    def get_access_specifier(self) -> cindex.AccessSpecifier:
        return self.access_specifier

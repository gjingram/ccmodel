from clang import cindex, enumerations
import typing

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.VAR_DECL)
class VariableObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.storage_class = node.storage_class.name
        self.attr = None
        self.member = False
        self.const = node.type.is_const_qualified()
        self.determine_scope_name(node)

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> typing.Union['VariableObject']:

        ParseObject.handle(self, node)

        for child in self.children(node, cindex.CursorKind.ANNOTATE_ATTR):
            self.setattr(child.displayname)

        if not self.is_member:
            self.header.header_add_variable(self)

        return self

    def is_member(self, isIt: bool) -> 'VariableObject':
        self.member = isIt
        return self

    def setattr(self, attr: str) -> None:
        self.attr = attr
        return


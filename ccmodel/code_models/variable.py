from clang import cindex, enumerations
import typing

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.VAR_DECL)
class VariableObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.storage_class = node.storage_class
        self.type = node.type.spelling
        self.attr = None
        self._is_member = False
        self.constness = 'const' in self.type

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> typing.Union['VariableObject']:

        ParseObject.handle(self, node)

        for child in self.children(node, cindex.CursorKind.ANNOTATE_ATTR):
            self.setattr(child.displayname)

        if not self.is_member:
            self.header.header_add_variable(self)

        return self

    @property
    def is_member(self, isIt: bool) -> 'VariableObject':
        self._is_member = isIt
        return self

    @is_member.getter
    def is_member(self) -> bool:
        return self._is_member

    def setattr(self, attr: str) -> None:
        self.attr = attr
        return


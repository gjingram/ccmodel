from clang import cindex, enumerations
import typing

from .decorators import if_handle, append_cpo, add_obj_to_header_summary
from .parse_object import ParseObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.VAR_DECL)
class VariableObject(ParseObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.info["attr"] = ""
        self.info["is_member"] = False
        self.info["is_const"] = (
            node.type.is_const_qualified() if node is not None else False
        )
        if node is not None:
            self.determine_scope_name(node)

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> typing.Union["VariableObject"]:

        if not self["is_member"]:
            ParseObject.handle(self, node)

        children = []
        self.extend_children(node, children)

        for child in self.children(children, cindex.CursorKind.ANNOTATE_ATTR):
            self.setattr(child.displayname)

        return self

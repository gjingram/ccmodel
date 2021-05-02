from clang import cindex, enumerations
import typing
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .variable import VariableObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.FIELD_DECL)
class MemberObject(VariableObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        VariableObject.__init__(self, node, force)
        self.info["access_specifier"] = (
            node.access_specifier.name if node is not None else ""
        )
        self["member"] = True
        if node is not None:
            self.determine_scope_name(node)

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "MemberObject":
        if (
            self["scope"]
            and not self["scope"]["export_to_scope"]
        ):
            self["scoped_id"] = "::".join([self["scope"]["scoped_id"], self["id"]])
            self["scoped_displayname"] = "::".join(
                [self["scope"]["scoped_displayname"], self["id"]]
            )
        VariableObject.handle(self, node)
        return self

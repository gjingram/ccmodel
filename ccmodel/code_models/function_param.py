from clang import cindex, enumerations
import typing
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject

from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.PARM_DECL)
class FunctionParamObject(ParseObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info["default"] = None
        self.info["function"] = None
        self["is_fparam"] = True
        if node is not None:
            self.determine_scope_name(node)
        return

    def set_scoped_id(self) -> "FunctionParamObject":
        self["scoped_id"] = self["function"]["scoped_id"] + "::{}".format(self["id"])
        self["scoped_displayname"] = self["function"][
            "scoped_displayname"
        ] + "::{}".format(self["id"])
        self["usr"] = self["scoped_displayname"]
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> "FunctionParamObject":
        return ParseObject.handle(self, node)

    def set_function(self, fn: "FunctionObject") -> "FunctionParamObject":
        self["function"] = fn
        return self

    def set_default_value(self, default: str) -> "FunctionParamObject":
        self["default"] = default
        return self

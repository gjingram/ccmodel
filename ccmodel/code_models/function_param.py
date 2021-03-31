from clang import cindex, enumerations
import typing
import pdb

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject

import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.PARM_DECL)
class FunctionParamObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.type = node.type.spelling
        self.default = None
        self.fn = None
        self.anonymous = False

        self.original_cpp_object = True

        return

    def set_qualified_id(self) -> 'FunctionParamObject':
        
        self.qualified_id = self.fn.qualified_id + "::{}".format(self.id)
        return self

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'FunctionParamObject':
        return ParseObject.handle(self, node)

    def set_function(self, fn: 'FunctionObject') -> 'FunctionParamObject':
        self.fn = fn
        return self

    def set_default_value(self, default: str) -> 'FunctionParamObject':
        self.default = default
        return self

    def get_default_value(self) -> str:
        return self.default

    def get_string_repr(self) -> str:
        out = self.type
        if self.anonymous:
            return out
        out += f" {self.id}"
        if self.default is not None:
            out += f" = {self.default}"
        return out

    def get_param_type(self) -> str:
        return x.type

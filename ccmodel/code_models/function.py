from clang import cindex, enumerations
import typing

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .function_param import FunctionParamObject
from ..rules import code_model_map as cmm

@cmm.default_code_model(cindex.CursorKind.FUNCTION_DECL)
class FunctionObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.storage_class = node.storage_class
        self.info = {}
        
        self.return_type = node.result_type.spelling
        self.info['return'] = self.return_type
        
        self.n_args = 0
        self.info['n_args'] = self.n_args

        self.info['args'] = {}
        self._is_member = False
        self._is_template = False
        self.name = self.id

        self.original_cpp_object = True

        return

    def __getitem__(self, item: str):
        try:
            out = self.info[item]
        except:
            try:
                out = self.info['args'][item]
            except:
                out = None

        return out

    def is_member(self, is_it: bool) -> 'FunctionObject':
        self._is_member = is_it
        return self

    def is_template(self, is_it: bool) -> 'FunctionObject':
        self._is_template = is_it
        return self

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'FunctionObject':

        self.header.register_object(self)
        if not self.is_definition:
            self.definition = self.header.get_usr(node.referenced.get_usr())

        types = []
        for child in self.children(node, cindex.CursorKind.PARM_DECL):
            types.append(child.type.spelling)
        old_qual_id = self.qualified_id
        self.qualified_id += f"({','.join(types)})"

        for child in node.get_children():

            if child.kind == cindex.CursorKind.PARM_DECL:

                using_cls = self.get_child_type(child)

                param_var = using_cls(child)
                
                if param_var.id == "":
                    param_var.id = "param{}".format(self.n_args)
                    param_var.displayname = param_var.id
                    param_var.anonymous = True

                param_var.set_function(self)
                param_var.set_header(self.header)
                param_var.set_scope(self)
                param_var.handle(child)

                self.add_function_param(param_var)

                arg_list = []
                for param_tok in child.get_tokens():
                    arg_list.append(param_tok)

                for argidx in range(0, len(arg_list)):
                    if arg_list[argidx].spelling == '=':
                        param_var.set_default_value(arg_list[argidx+1].spelling)

        if not self._is_member and not self._is_template:
            self.header.header_add_function(self)

        self.qualified_id = old_qual_id

        return self

    def add_function_param(self, param: FunctionParamObject) -> None:
        self.info['args'][param.get_name()] = param
        self.n_args += 1
        self.info['n_args'] = self.n_args
        return

    def get_function_params(self) -> typing.Tuple[FunctionParamObject]:
        return tuple(self.par)

from clang import cindex, enumerations
import typing
import pdb

from .decorators import (if_handle, append_cpo,
        add_obj_to_header_summary)
from .parse_object import ParseObject
from .function_param import FunctionParamObject
from ..rules import code_model_map as cmm

@cmm.default_code_model(cindex.CursorKind.FUNCTION_DECL)
class FunctionObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info['return'] = node.result_type.spelling if node is not None else ""
        self.info['n_params'] = 0
        self.info['params'] = {}
        self.info["is_member"] = False
        self.info["template_ref"] = None
        if node is not None:
            self.determine_scope_name(node)
        return

    def set_template_ref(self, templ: 'TemplateObject') -> 'FunctionObject':
        self["is_template"] = True
        self["template_ref"] = templ
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'FunctionObject':

        if not self["is_member"] and not self["is_template"]:
            ParseObject.handle(self, node)

        children = []
        self.extend_children(node, children)

        self["header"].register_object(self)
        if not self["is_definition"]:
            self["definition"] = self["header"].get_usr(node.referenced.get_usr())

        types = []
        for child in self.children(children, cindex.CursorKind.PARM_DECL):
            types.append(child.type.spelling)

        for child in children:

            if child.kind == cindex.CursorKind.PARM_DECL:

                using_cls = self.get_child_type(child)
                param_var = using_cls(child)
                
                if param_var["id"] == "":
                    param_var["id"] = "param{}".format(self["n_params"])
                    param_var["displayname"] = param_var["id"]
                    param_var["scoped_displayname"] = param_var["displayname"]
                    param_var["is_anonymous"] = True

                param_var.set_function(self)
                param_var.set_header(self["header"])
                param_var.add_template_parents(self["template_parents"])
                param_var.set_scope(self)
                param_var.set_scoped_id()
                param_var.handle(child)

                self.add_function_param(param_var)

                arg_list = []
                for param_tok in child.get_tokens():
                    arg_list.append(param_tok)

                for argidx in range(0, len(arg_list)):
                    if arg_list[argidx].spelling == '=':
                        param_var.set_default_value(arg_list[argidx+1].spelling)
        return self

    def add_function_param(self, param: FunctionParamObject) -> None:
        self["params"][param.get_name()] = param
        self["n_params"] += 1
        return

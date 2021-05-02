from clang import cindex, enumerations
import typing
import pdb

from .decorators import if_handle, append_cpo, add_obj_to_header_summary
from .parse_object import ParseObject
from .function_param import FunctionParamObject
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser
from ..utils.code_utils import (
    split_bracketed_list,
    replace_template_params_str
)


@cmm.default_code_model(cindex.CursorKind.FUNCTION_DECL)
class FunctionObject(ParseObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info["return"] = node.result_type.spelling if node is not None else ""
        self.info["n_params"] = 0
        self.info["params"] = {}
        self.info["is_member"] = False
        self.info["template_ref"] = None
        self["is_function"] = True
        if node is not None:
            self.determine_scope_name(node)
        return

    def set_template_ref(self, templ: "TemplateObject") -> "FunctionObject":
        self["is_template"] = True
        self["template_ref"] = templ
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> "FunctionObject":

        if self["is_template"]:
            params = ", ".join(split_bracketed_list(self["displayname"],
                brack="()",
                blevel=-1))
            self["displayname"] = self["template_ref"]["displayname"] + \
                    "(" + params + ")"
            self["scoped_displayname"] = self["template_ref"]["scoped_displayname"] + \
                    "(" + params + ")"
            self["scoped_displayname"] = replace_template_params_str(
                self["scoped_displayname"],
                self["template_parents"])

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

                header_use = parser.get_header(child.location.file.name)
                param_var.set_function(self)
                param_var.set_header(header_use)
                param_var.add_template_parents(self["template_parents"])
                param_var.set_scope(self)
                param_var.add_active_namespaces(self.active_namespaces)
                param_var.add_active_directives(self.active_using_directives)
                param_var.set_parse_level(self["parse_level"])
                param_var.set_scoped_id()
                param_var.do_handle(child)
                param_var.handle(child)

                self.add_function_param(param_var)

                arg_list = []
                for param_tok in child.get_tokens():
                    arg_list.append(param_tok)

                for argidx in range(0, len(arg_list)):
                    if arg_list[argidx].spelling == "=":
                        param_var.set_default_value(arg_list[argidx + 1].spelling)
        return self

    def add_function_param(self, param: FunctionParamObject) -> None:
        self["params"][param.get_name()] = param
        self["n_params"] += 1
        self["all_objects"].append(param)
        return

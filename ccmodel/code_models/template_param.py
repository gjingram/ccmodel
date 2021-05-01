from clang import cindex, enumerations
import typing
import regex

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from ..rules import code_model_map as cmm
from ..utils.code_utils import replace_template_params_str

import pdb

re_param = regex.compile("(?:\[(?P<default>.*)\])")

template_type_param = r"(?P<template_def>^template\s*<(?P<t_arglist>\s*.*\s*)>)?\s*"
template_type_param += r"(?:class|typename)\s*(?<ellipsis>\.{3}\s*)?"
template_type_param += r"(?P<name>(?::{2})?\w\w*(?::{2}\w*)*(?:<(?:.*)>)?)?"
template_type_param += r"(?:\s*=\s*(?P<default>.*$))?"
template_nontype_param = r"(?P<type>\w*)\s*(?P<name>\w*)(?:\s*=\s*(?P<default>.*$))?"

re_type_param = regex.compile(template_type_param)
re_nontype_param = regex.compile(template_nontype_param)


@cmm.default_code_model(cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER)
@cmm.default_code_model(cindex.CursorKind.TEMPLATE_TYPE_PARAMETER)
@cmm.default_code_model(cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER)
class TemplateParamObject(ParseObject):
    def __init__(self, tparent: "TemplateObject", node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.info["param_type"] = node.kind.name if node is not None else ""
        self.info["template"] = tparent
        self.info["object"] = None
        self.info["default"] = None
        self.info["is_variadic"] = False
        self.info["is_type_param"] = False
        self.info["is_non_type_param"] = False
        self.info["is_template_template_param"] = False
        self.info["template_ref"] = None
        self.info["optional"] = False
        self.info["parameter"] = None

        anon_by_def = self["id"] == ""
        if self["id"] == "":
            self["id"] = f"param{self['template']['n_template_parameters']}"
            self["displayname"] = self["id"]
        if node is not None:
            self.determine_scope_name(node)
        if self["usr"] == "":
            self["usr"] = self["scoped_displayname"]
        self["scoped_displayname"] = (
            self["template"]["scoped_displayname"] + "::" + self["id"]
        )
        self.template_params_replaced = True

        if node is not None:
            self.handle_parameter(node)
        self.parameter_set = False

        children = []
        if node is not None:
            self.extend_children(node, children)

        self.type = ""
        self.param = ""
        if self["param_type"] == "TEMPLATE_TEMPLATE_PARAMETER":
            self["is_template_template_param"] = True
            if node is not None:
                self.type = "<#>" if node.spelling == "" else node.spelling
            self.param = f"<#>"
        elif self["param_type"] == "TEMPLATE_TYPE_PARAMETER":
            self["is_type_param"] = True
            if node is not None:
                self.type = (
                    "#" if node.spelling == node.type.spelling else node.type.spelling
                )
            self.param = "#"
        elif self["param_type"] == "TEMPLATE_NON_TYPE_PARAMETER":
            pdb.set_trace()
            self["is_non_type_param"] = True
            self.type = node.type.spelling if node is not None else ""
            self.param = f"{self.type}#"

        if self["is_template_template_param"]:
            if node is not None:
                for child in self.children(children, cindex.CursorKind.TEMPLATE_REF):
                    self["default"] = self["header"].header_get_usr(child.get_usr())
        if self["is_variadic"]:
            self.param = self.param.replace("#", "[#]")
            self["optional"] = True
        if self["default"] is not None and not anon_by_def:
            self["default"] = replace_template_params_str(
                    self["default"],
                    [*self["template"]["template_parents"], self["template"]]
                    )
            self.param = self.param.replace(f"{self.type}#", f'[{self["default"]}]')
            self["optional"] = True
        if anon_by_def:
            self["optional"] = True
            if self["default"]:
                self["default"] = replace_template_params_str(
                        self["default"],
                        [*self["template"]["template_parents"], self["template"]]
                        )
                self.param = self.param.replace("#", f"[{self['default']}]")

        self["parameter"] = self.param
        self["type"] = self.type

        return

    def handle_parameter(self, node: cindex.Cursor) -> None:
        toks = list(node.get_tokens())
        param_str = ""

        # Handling some real clang bullshit right here.
        for tok in toks:
            if tok.spelling == "<<":
                param_str += "<"
            elif tok.spelling == ">>":
                param_str += ">"
            else:
                param_str += tok.spelling
        tmatch = re_type_param.search(param_str)

        if tmatch is not None:
            tmatch_groups = tmatch.groupdict()
            if "default" in tmatch_groups and tmatch_groups["default"] is not None:
                self.set_default_value(tmatch_groups["default"])
            if "..." in param_str:
                self.is_variadic(True)
            return

        ntmatch = re_nontype_param.search(param_str)
        if ntmatch is not None:
            ntmatch_groups = ntmatch.groupdict()
            if "default" in ntmatch_groups and ntmatch_groups["default"] is not None:
                self.set_default_value(ntmatch_groups["default"])

        return

    def set_scoped_id(self) -> "TemplateParamObject":
        self["scoped_id"] = self["template"]["scoped_id"] + "::{}".format(self["id"])
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> "TemplateParamObject":
        return ParseObject.handle(self, node)

    def set_template(self, template: "TemplateObject") -> "TemplateParamObject":
        self["template"] = template
        return self

    def set_default_value(self, val: str) -> "TemplateParamObject":
        self["default"] = str(val)
        return self

    def is_variadic(self, is_it: bool) -> "TemplateParamObject":
        self["is_variadic"] = is_it
        return self

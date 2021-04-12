from clang import cindex, enumerations
import typing
import regex

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject, re_targlist
from ..rules import code_model_map as cmm

import pdb

re_param = regex.compile('(?:\[(?P<default>.*)\])')

template_type_param = r"(?P<template_def>^template\s*<(?P<t_arglist>\s*.*\s*)>)?\s*"
template_type_param += r"(?:class|typename)\s*(?<ellipsis>\.{3}\s*)?"
template_type_param += r"(?P<name>(?::{2})?\w\w*(?::{2}\w*)*(?:<(?:.*)>)?)"
template_type_param += r"(?:\s*=\s*(?P<default>.*$))?"
template_nontype_param = r"(?P<type>\w*)\s*(?P<name>\w*)(?:\s*=\s*(?P<default>.*$))?"

re_type_param = regex.compile(template_type_param)
re_nontype_param = regex.compile(template_nontype_param)

@cmm.default_code_model(cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER)
@cmm.default_code_model(cindex.CursorKind.TEMPLATE_TYPE_PARAMETER)
@cmm.default_code_model(cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER)
class TemplateParamObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.param_type = node.kind
        self.template = None
        self.obj = None
        self.type = None
        self.default_value = None
        self._is_variadic = False
        
        self.is_type_param = False
        self.is_non_type_param = False
        self.is_template_template_param = False
        self.template_ref = None
        self.optional = False

        self.determine_scope_name(node)

        self.param = None

        self.handle_parameter(node)
        
        self.original_cpp_object = True
        if self.param_type == cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
            self.is_template_template_param = True
            self.type = "#" if node.spelling == "" else node.spelling
            self.param = f"#"
        elif self.param_type == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
            self.is_type_param = True
            self.type = "#" if node.spelling == node.type.spelling else node.type.spelling
            self.param = "#"
        elif self.param_type == cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
            self.is_non_type_param = True
            self.type = node.type.spelling
            self.param = f"{self.type}#"

        if self.is_template_template_param:
            for child in self.children(node, cindex.CursorKind.TEMPLATE_REF):
                self.default_value = self.header.header_get_usr(child.get_usr())
        if self._is_variadic:
            self.param = self.param.replace('#', '[#...]')
            self.optional = True
        if self.default_value is not None:
            self.param = self.param.replace('#', f'[{self.default_value}]')
            self.optional = True

        return

    def handle_parameter(self, node: cindex.Cursor) -> None:
        #toks = [x.spelling for x in node.get_tokens()]
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
            if "ellipsis" in tmatch_groups and tmatch_groups["ellipsis"] is not None:
                self.is_variadic(True)
            return

        ntmatch = re_nontype_param.search(param_str)
        if ntmatch is not None:
            ntmatch_groups = ntmatch.groupdict()
            if "default" in ntmatch_groups and ntmatch_groups["default"] is not None:
                self.set_default_value(ntmatch_groups["default"])

        return

    def set_scoped_id(self) -> 'TemplateParamObject':
        self.scoped_id = self.template.scoped_id + "::{}".format(self.id)
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'TemplateParamObject':
        return ParseObject.handle(self, node)

    def set_template(self, template: 'TemplateObject') -> 'TemplateParamObject':
        self.template = template
        return self

    def get_type(self) -> str:
        return self.type

    def set_default_value(self, val: str) -> 'TemplateParamObject':
        self.default_value = str(val)
        return self

    def get_default_value(self) -> str:
        return self.default_value

    def is_variadic(self, is_it: bool) -> 'TemplateParamObject':
        self.variadic = is_it
        return self

    @property
    def variadic(self) -> bool:
        return self._is_variadic

    @variadic.setter
    def variadic(self, is_it: bool) -> None:
        self._is_variadic = is_it
        return

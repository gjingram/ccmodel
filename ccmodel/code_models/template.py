from clang import cindex, enumerations
import typing
import pdb
import regex

from .decorators import (if_handle, 
        append_cpo)
from .parse_object import ParseObject, replace_template_params, split_template_list
from .template_param import TemplateParamObject
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE)
@cmm.default_code_model(cindex.CursorKind.FUNCTION_TEMPLATE)
class TemplateObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.obj = None
        self.obj_class = None
        self.is_alias = False

        self.template_parameters = []
        self.is_primary = True
        self.is_partial = False
        self.template_ref = None
        self.n_template_params = -1
        self.primary_ref = None
        self._is_method_template = False
        self._is_function_template = False

        return

    def is_function_template(self, is_it: bool) -> 'TemplateObject':
        self._is_function_template = is_it
        return self

    def is_method_template(self, is_it: bool) -> 'TemplateObject':
        self._is_method_template = is_it
        return self

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TemplateObject':

        replace_template_params(self)
        node_children = []
        for child in node.get_children():

            if child.kind == cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            else:
                continue

        self.scoped_displayname = self.scoped_id + f"<{','.join([x.param for x in self.template_parameters])}>"
        for child_node, param in zip(node_children, self.template_parameters):
            param.scoped_displayname = self.scoped_displayname + "::" + param.id
            param.handle(child_node)

        tparents = [*self.template_parents, self]
        if self.scoped_id in cmm.object_code_models:
            self.obj_class = cmm.object_code_models[self.scoped_id]
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE:
            self.obj_class = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self.obj = self.obj_class(node, True).add_template_parents(tparents)\
                    .set_header(self.header).set_scope(self.scope).set_template_ref(self).handle(node)
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
            self.is_partial = True
            self.obj_class = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self.obj = self.obj_class(node, True).add_template_parents(tparents)\
                    .set_header(self.header).set_scope(self.scope).set_template_ref(self).handle(node)
        elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            if self._is_function_template:
                self.obj_class = cmm.default_code_models[cindex.CursorKind.FUNCTION_DECL]
            elif self._is_method_template:
                self.obj_class = cmm.default_code_models[cindex.CursorKind.CXX_METHOD]
            self.obj = self.obj_class(node, True).add_template_parents(tparents)\
                    .set_header(self.header).set_scope(self.scope).set_template_ref(self).handle(node)
        else:
            if self.is_partial:
                return None

        self.header.register_object(self)
        if not self.is_definition:
            self.definition = self.header.get_usr(node.referenced.get_usr())
        
        self.n_template_params = len(self.template_parameters)
        self.resolve_primary_ref()

        
        return self

    def handle_template_parameter(self, node: cindex.Cursor) -> None:

        using_cls = self.get_child_type(node)

        template_param = using_cls(node)
        template_param.set_header(self.header)
        template_param.set_scope(self.scope)
        template_param.obj = self.obj
        template_param.template = self
        self.add_template_param(template_param)

        return

    def add_template_param(self, param: typing.Union['TemplateObject', 'TemplateParamObject']) -> None:
        self.template_parameters.append(param)
        return

    def resolve_primary_ref(self) -> None:
        if self.is_primary:
            self.primary_ref = self
            self.header.template_specializations[self.scoped_id] = {}
            self.header.template_specializations[self.scoped_id][tuple([x.param for x in self.template_parameters])] = \
                    self
            return
        elif not self.is_alias:
            specializations = self.header.template_specializations[self.scoped_id]
            for spec in specializations.values():
                if spec.is_primary:
                    self.primary_ref = spec
        else:
            self.primary_ref = None

        return

template_decl = r"\btemplate\s*<(?P<t_arglist>.*)>(?=\s*(:{2})?\w)"
template_type_param = r"(?P<template_def>^template\s*<(?P<t_arglist>\s*.*\s*)>)?\s*"
template_type_param += r"(?:class|typename)\s*(?:\.{3}\s*)?(?P<name>\w*)(?:\s*=\s*(?P<default>.*$))?"
template_nontype_param = r"(?P<type>\w*)\s*(?P<name>\w*)(?:\s*=\s*(?P<default>.*$))?"
template_class = r"(?:class|struct)\s*(?P<cls_name>\w*)\s*<(?P<t_arglist>.*)>"
template_alias = r"using\s*(?P<alias>\w*)\s*=\s*(?P<cls_name>\w*)\s*(?:<(?P<t_arglist>.*)>)?"

re_template_decl = regex.compile(template_decl)
re_type_param = regex.compile(template_type_param)
re_nontype_param = regex.compile(template_nontype_param)
re_template_class = regex.compile(template_class)
re_template_alias = regex.compile(template_alias)

class TemplateParamTypes:
    TYPE = 0
    NONTYPE = 1
    TEMPLATE = 2

@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION)
class PartialSpecializationObject(TemplateObject):
    
    def __init__(self, node: cindex.CursorKind, force: bool = False):
        TemplateObject.__init__(self, node, force)
        self.is_primary = False
        self.is_partial = True
        self.partial_ref = None
        self.is_alias = False
        self.partial_text = " ".join([x.spelling for x in node.get_tokens()])

        self._template_decl_params = []
        self._class_arglist = []
        self._primary_name = ""

        return

    def add_template_decl_param(self, kind: int, ptype: str, name: str) -> None:
        ptype_use = ptype.replace(' ', '')
        name_use = name.replace(' ', '')
        self._template_decl_params.append((kind, ptype_use, name_use))
        return

    def process_template_paramlist(self, paramlist) -> None:
        pmatches = split_template_list(paramlist)
        for pmatch in pmatches:
            tmatch = re_type_param.match(pmatch)
            ntmatch = re_nontype_param.match(pmatch)
            if tmatch is not None:
                tmatch_groupdict = tmatch.groupdict()
                if "template_def" in tmatch_groupdict and tmatch_groupdict["template_def"] is not None:
                    self.add_template_decl_param(TemplateParamTypes.TEMPLATE, "~",
                            tmatch.group('name'))
                elif "name" in tmatch_groupdict and tmatch_groupdict["name"] is not None:
                    self.add_template_decl_param(TemplateParamTypes.TYPE, "~",
                            tmatch.group('name'))
            elif ntmatch is not None:
                self.add_template_decl_param(TemplateParamTypes.NONTYPE,
                        ntmatch.group('type'), ntmatch.group('name'))
        return

    def process_class_template_arglist(self, carglist) -> None:
        amatches = split_template_list(carglist)
        for amatch in amatches:
            self._class_arglist.append(amatch.replace(' ', ''))
        return

    def parse_template_decl(self) -> None:
        tmatch = re_template_decl.search(self.partial_text)
        self.process_template_paramlist(tmatch.group('t_arglist'))
        cmatch = None
        if not self.is_alias:
            cmatch = re_template_class.search(self.partial_text)
        else:
            cmatch = re_template_alias.search(self.partial_text)
        if cmatch is not None:
            self._primary_name = cmatch.group('cls_name')
            if "t_arglist" in cmatch.groupdict() and cmatch.groupdict()["t_arglist"] is not None:
                self.process_class_template_arglist(cmatch.group('t_arglist'))

        for pidx, param in enumerate(self._class_arglist):
            for tparam in self._template_decl_params:
                if param == tparam[2]:
                    self._class_arglist[pidx] = "~"
        return

    def extract_params(self) -> typing.Tuple[str]:
        return tuple((arg for arg in self._class_arglist))

    def handle(self, node: cindex.Cursor) -> 'PartialSpecializationObject':
        replace_template_params(self)
        TemplateObject.handle(self, node)
        self.parse_template_decl()
        self.partial_ref = \
                self.header.header_match_template_ref(self._primary_name, self.extract_params())
        self.dep_objs.append(self.partial_ref)
        self.scoped_displayname
        return self



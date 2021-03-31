from clang import cindex, enumerations
import typing
import pdb

from illuminate.code_models.decorators import (if_handle, 
        append_cpo)
from illuminate.code_models.parse_object import ParseObject
from illuminate.code_models.template_param import TemplateParamObject
import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE)
@cmm.default_code_model(cindex.CursorKind.FUNCTION_TEMPLATE)
@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION)
class TemplateObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.obj = None
        self.obj_class = None
        self.is_alias = False

        self.template_parameters = []
        self.is_partial = False
        self.template_ref = None

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TemplateObject':

        if self.qualified_id in cmm.object_code_models:
            self.obj_class = cmm.object_code_models[self.qualified_id]
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE:
            self.obj_class = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
            self.is_partial = True
            self.obj_class = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
        elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            self.obj_class = cmm.default_code_models[cindex.CursorKind.FUNCTION_DECL]
        else:
            return None

        ParseObject.handle(self, node)
        self.obj = self.obj_class(node).set_header(self.header).set_scope(self.scope).is_template(True).handle(node)

        for child in node.get_children():

            if child.kind == cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
                self.handle_template_parameter(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
                self.handle_template_parameter(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                self.handle_template_parameter(child)

            else:
                continue

        return self

    def handle_template_parameter(self, node: cindex.Cursor) -> None:

        using_cls = self.get_child_type(node)

        template_param = using_cls(node)
        template_param.set_header(self.header)
        template_param.set_scope(self.scope)
        template_param.obj = self.obj
        template_param.template = self
        template_param.handle(node)

        toks = list(node.get_tokens())
        for tok_idx, tok in enumerate(toks):

            if toks[tok_idx-1].spelling == template_param.get_name() and \
                tok.spelling == '=':

                template_param.set_default_value(toks[tok_idx+1].spelling)

            if tok.spelling == "...":
                template_param.is_variadic(True)

        self.add_template_param(template_param)

        return

    def add_template_param(self, param: typing.Union['TemplateObject', 'TemplateParamObject']) -> None:
        self.template_parameters.append(param)
        return

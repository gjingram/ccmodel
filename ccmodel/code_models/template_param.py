from clang import cindex, enumerations
import typing

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
import illuminate.rules.code_model_map as cmm


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

        self.original_cpp_object = True

        if self.param_type == cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
            self.is_template_template_param = True
        elif self.param_type == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
            self.is_type_param = True
        elif self.param_type == cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
            self.is_non_type_param = True
            self.type = node.spelling

        return

    def set_qualified_id(self) -> 'TemplateParamObject':
        self.qualified_id = self.template.qualified_id + "::{}".format(self.id)
        return self

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'TemplateParamObject':
        if self.is_template_template_param:
            for child in self.children(node, cindex.CursorKind.TEMPLATE_REF):
                self.default_value = self.header.header_get_usr(child.get_usr())
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

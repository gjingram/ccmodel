from clang import cindex, enumerations
import typing
import re

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject, \
        python_var_pattern
from illuminate.code_models.function import FunctionObject
from illuminate.code_models.types import ClassType

import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CONSTRUCTOR)
@cmm.default_code_model(cindex.CursorKind.DESTRUCTOR)
@cmm.default_code_model(cindex.CursorKind.CXX_METHOD)
@cmm.default_code_model(cindex.CursorKind.CONVERSION_FUNCTION)
class MemberFunctionObject(FunctionObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        FunctionObject.__init__(self, node, force)
        
        self.access_specifier = node.access_specifier
        self.is_const = node.is_const_method()
        self.is_ctor = False
        self.is_dtor = False
        self.is_conversion = False
        self.converting_ctor = node.is_converting_constructor()
        self.is_pure_virtual = node.is_pure_virtual_method()
        self.is_static = node.is_static_method()
        self.is_virtual = node.is_virtual_method()
        self.is_final = False
        self.is_override = False

        self.original_cpp_object = True
        self.displayname = (self.displayname + " const") if self.is_const else \
                self.displayname

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'MemberFunctionObject':

        FunctionObject.is_member(self, True)
        FunctionObject.handle(self, node)

        if self.is_pure_virtual:
            self.scope.set_class_type(ClassType.ABSTRACT)
        elif self.is_virtual:
            self.scope.set_class_type(ClassType.VIRTUAL)
        else:
            self.scope.set_class_type(ClassType.CONCRETE)

        for child in node.get_children():
            if child.kind == cindex.CursorKind.CXX_FINAL_ATTR and not self.is_final:
                self.is_final = True
            if child.kind == cindex.CursorKind.CXX_OVERRIDE_ATTR and not self.is_override:
                self.is_override = True

        return self

    def get_access_specifier(self) -> int:
        return self.access_specifier

    def mark_ctor(self, is_it: bool) -> 'MemberFunctionObject':
        self.is_ctor = is_it
        return self

    def mark_dtor(self, is_it: bool) -> 'MemberFunctionObject':
        self.is_dtor = is_it
        return self

    def mark_conversion(self, is_it: bool) -> 'MemberFunctionObject':
        self.is_conversion(is_it)
        return self

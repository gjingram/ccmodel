from clang import cindex, enumerations
import typing
import pdb

from illuminate.code_models.decorators import (if_handle, 
        append_cpo)
from illuminate.code_models.parse_object import ParseObject
from illuminate.code_models.namespace import NamespaceObject
from illuminate.code_models.member import MemberObject
from illuminate.code_models.member_function import MemberFunctionObject
from illuminate.code_models.types import ClassType
import illuminate.rules.code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CLASS_DECL)
@cmm.default_code_model(cindex.CursorKind.STRUCT_DECL)
class ClassObject(NamespaceObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        NamespaceObject.__init__(self, node, force)

        self.class_constructors = []
        self.class_destructors = []
        self.class_conversion_functions = []
        self.class_type = ClassType.CONCRETE
        self.class_parent_types = []

        self.class_type = ClassType.CONCRETE
        self._is_template = False

        self.original_cpp_object = True
        self.is_final = False
        

        return

    def create_clang_child_object(self, node: cindex.Cursor) -> 'ParseObject':
        cpo_class = self.get_child_type(node)
        return cpo_class(node, self.force_parse).set_header(self.header).set_scope(self).handle(node)

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'ClassObject':

        ParseObject.handle(self, node) 
        for child in node.get_children():

            # Resolve parent ClassObject when creating module links
            if child.kind == cindex.CursorKind.CXX_BASE_SPECIFIER:
                self.add_class_parent_type(child)
                continue

            if child.kind == cindex.CursorKind.CONSTRUCTOR:
                ctor = self.create_clang_child_object(child).mark_ctor(True)
                self.add_class_constructor(ctor)
                if ctor.converting_ctor:
                    self.add_class_conversion_function(ctor)
                continue

            if child.kind == cindex.CursorKind.DESTRUCTOR:
                self.add_class_destructor(self.create_clang_child_object(child).mark_dtor(True))
                continue

            if child.kind == cindex.CursorKind.FIELD_DECL:
                self.add_variable(self.create_clang_child_object(child))
                continue

            if child.kind == cindex.CursorKind.CXX_METHOD:
                self.add_function(self.create_clang_child_object(child))
                continue

            if child.kind == cindex.CursorKind.CONVERSION_FUNCTION:
                self.add_class_conversion_function(self.create_clang_child_object(child).mark_conversion(True))
                continue

            if child.kind == cindex.CursorKind.CXX_FINAL_ATTR and not self.is_final:
                self.is_final = True

        if not self._is_template:
            self.header.header_add_class(self)

        return self

    def is_template(self, is_it: bool) -> 'ClassObject':
        self._is_template = is_it
        return self

    def add_class_parent_type(self, class_in: cindex.CursorKind) -> None:
        self.class_parent_types.append(self.header.header_get_dep(class_in, self))
        return

    def add_class_constructor(self, ctor: 'MemberFunctionObject') -> None:
        self.class_constructors.append(ctor)
        return

    def add_class_destructor(self, dtor: 'MemberFunctionObject') -> None:
        self.class_destructors.append(dtor)
        return

    def add_class_conversion_function(self, conv: 'MemberFunctionObject') -> None:
        self.class_conversion_functions.append(conv)
        return

    def set_class_type(self, type_in: int) -> None:
        self.class_type = type_in if type_in > self.class_type else self.class_type
        return

    def get_parent_types(self) -> typing.Tuple[str]:
        return (dep.dep_name for dep in self.object_dependencies)

    def get_parent_objects(self) -> typing.Tuple['ClassObject']:
        return (dep.parse_object for dep in self.object_dependencies)

    def get_class_dependencies_resolved(self) -> bool:
        deps_resolved = True
        for dep in self.object_dependencies:
            deps_resolved &= dep.dependency_resolved
        return deps_resolved

from clang import cindex, enumerations
import os
import typing
import pdb

from .decorators import (if_handle,
        append_cpo)
from .parse_object import ParseObject, replace_template_params
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.NAMESPACE)
class NamespaceObject(ParseObject):

    def __init__(self, node: typing.Union[cindex.Cursor, None], force: bool = False):
        ParseObject.__init__(self, node, force)

        if not node:
            self.displayname = 'GlobalNamespace'
            self.id = 'GlobalNamespace'
            self.scoped_id = 'GlobalNamespace'
            self.scoped_displayname = 'GlobaleNamespace'
            self.scope = None
            self.kind = cindex.CursorKind.NAMESPACE

        self.header = None
        self.original_cpp_object = True

        if not self.scope:
            self.set_scope(self)

        self.namespaces = []
        self.class_templates = []
        self.function_templates = []
        self.typedefs = []
        self.classes = []
        self.structs = []
        self.unions = []
        self.functions = []
        self.enumerations = []
        self.namespace_aliases = []
        self.type_aliases = []
        self.type_alias_templates = []
        self.using_directives = []
        self.using_declarations = []
        self.variables = []

        self.identifier_map = {}
        self.usr_map = {}
        self.all_objects = []

        self._is_class = False

        self.is_namespace = True
        self.determine_scope_name(node)

        return

    def __getitem__(self, item) -> 'ParseObject':
        name_compare = item[0].replace(' ', '')
        if name_compare in self.identifier_map:
            return self.usr_map[self.identifier_map[name_compare]]

    def add_namespace(self, ns: 'NamespaceObject') -> None:
        self.namespaces.append(ns)
        return

    def add_class_template(self, ct: 'TemplateObject') -> None:
        self.class_templates.append(ct)
        return

    def add_function_template(self, ft: 'TemplateObject') -> None:
        self.function_templates.append(ft)
        return

    def add_typedef(self, td: 'TypeDefObject') -> None:
        self.typedefs.append(td)
        return

    def add_class(self, cls: 'ClassObject') -> None:
        self.classes.append(cls)
        return

    def add_struct(self, struct: 'ClassObject') -> None:
        self.classes.append(struct)
        return

    def add_union(self, union: 'UnionObject') -> None:
        self.unions.append(union)
        return

    def add_function(self, func: 'FunctionObject') -> None:
        self.functions.append(func)
        return

    def add_enumeration(self, enum: 'EnumObject') -> None:
        self.enumerations.append(enum)
        return

    def add_namespace_alias(self, ns_alias: 'NamespaceAliasObject') -> None:
        self.namespace_aliases.append(ns_alias)
        return

    def add_type_alias(self, t_alias: 'TypeAliasObject') -> None:
        self.type_aliases.append(t_alias)
        return

    def add_type_alias_template(self, tt_alias: 'TemplateTypeAliasObject') -> None:
        self.type_alias_templates.append(tt_alias)
        return

    def add_using_directive(self, u_dir: 'UsingNamespaceObject') -> None:
        self.using_directives.append(u_dir)
        return

    def add_using_decl(self, u_decl: 'UsingDeclarationObject') -> None:
        self.using_declarations.append(u_decl)
        return

    def add_variable(self, var: 'VariableObject') -> None:
        self.variables.append(var)
        return

    def add_object(self, add_method, node: cindex.Cursor) -> None:
        obj = self.create_clang_child_object(node)
        if obj is None:
            return
        add_method(obj)
        self.identifier_map[obj.scoped_id] = obj.usr
        self.usr_map[obj.usr] = obj
        self.all_objects.append(obj)
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'NamespaceObject':

        ParseObject.handle(self, node)

        tparents = [*self.template_parents, self.template_ref] if \
                self.is_template else self.template_parents

        for child in node.get_children():

            if child.kind == cindex.CursorKind.NAMESPACE:
                self.add_object(self.add_namespace, child)   

            if child.kind == cindex.CursorKind.CLASS_TEMPLATE:

                actually_method = cindex.CursorKind.PARM_DECL in [x.kind for x in child.get_children()]
                if actually_method:
                    self.handle_function_template(child)
                    continue

                cls_temp_obj = self.get_child_type(child)
                class_template = cls_temp_obj(child).add_template_parents(tparents)\
                        .set_header(self.header).set_scope(self).handle(child)
                if class_template is None:
                    continue
                self.header.header_add_template_class(class_template)

                self.add_class_template(class_template)
                self.identifier_map[class_template.scoped_id] = class_template.usr
                self.usr_map[class_template.usr] = class_template
                self.all_objects.append(class_template)

            if child.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:

                cls_temp_spec = self.get_child_type(child)
                cls_template_spec = cls_temp_spec(child).add_template_parents(tparents)\
                        .set_header(self.header).set_scope(self).handle(child)
                if cls_template_spec is None:
                    continue
                cls_template_spec.is_partial = True
                self.header.header_add_template_class(cls_template_spec)

                self.add_class_template(cls_template_spec)
                self.identifier_map[cls_template_spec.scoped_id] = cls_template_spec.usr
                self.usr_map[cls_template_spec.usr] = cls_template_spec
                self.all_objects.append(cls_template_spec)

            if child.kind == cindex.CursorKind.TYPEDEF_DECL:

                # Catch C typdef struct
                if child.underlying_typedef_type.spelling.startswith('struct '):
                    struct_object = self.create_clang_child_object(child)
                    if struct_object is None:
                        continue
                    self.add_struct(struct_object)
                    self.identifier_map[struct_object.scoped_id] = struct_object.usr
                    self.usr_map[struct_object.usr] = struct_object
                    self.all_objects.append(struct_object)
                else:
                    typedef = self.create_clang_child_object(child)
                    if typedef is None:
                        continue
                    self.add_typedef(typedef)
                    self.identifier_map[typedef.scoped_id] = typedef.usr
                    self.usr_map[typedef.usr] = typedef
                    self.all_objects.append(typedef)

            if child.kind == cindex.CursorKind.CLASS_DECL:
                self.add_object(self.add_class, child)

            if child.kind == cindex.CursorKind.STRUCT_DECL:
                self.add_object(self.add_struct, child)
            
            if child.kind == cindex.CursorKind.UNION_DECL:
                self.add_object(self.add_union, child)
     
            if child.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
                self.handle_function_template(child)
                continue

            if child.kind == cindex.CursorKind.ENUM_DECL:
                self.add_object(self.add_enumeration, child)

            if child.kind == cindex.CursorKind.FUNCTION_DECL:
                self.add_object(self.add_function, child)

            if child.kind == cindex.CursorKind.VAR_DECL:
                self.add_object(self.add_variable, child)
            
            if child.kind == cindex.CursorKind.NAMESPACE_ALIAS:
                self.add_object(self.add_namespace_alias, child)

            if child.kind == cindex.CursorKind.TYPE_ALIAS_DECL:
                self.add_object(self.add_type_alias, child)

            if child.kind == cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL:
                temp_alias_obj = self.get_child_type(child)
                alias_template = temp_alias_obj(child).add_template_parents(tparents)\
                        .set_header(self.header).set_scope(self).handle(child)
                if alias_template is None:
                    continue
                self.add_type_alias_template(alias_template)
                self.identifier_map[alias_template.scoped_id] = alias_template.usr
                self.usr_map[alias_template.usr] = alias_template
                self.all_objects.append(alias_template)

            if child.kind == cindex.CursorKind.USING_DIRECTIVE:
                self.add_object(self.add_using_directive, child)

            if child.kind == cindex.CursorKind.USING_DECLARATION:
                self.add_object(self.add_using_decl, child)

        self.header.header_add_namespace(self)
        return self

    def handle_function_template(self, child: cindex.Cursor) -> None:
        tparents = [*self.template_parents, self.template_ref] if self.is_template else self.template_parents
        fn_temp_obj = self.get_child_type(child)
        function_template = None
        if not self._is_class:
            function_template = fn_temp_obj(child).add_template_parents(tparents)\
                    .set_header(self.header).set_scope(self)\
                    .is_function_template(True).handle(child)
        else:
            function_template = fn_temp_obj(child).add_template_parents(tparents)\
                    .set_header(self.header).set_scope(self)\
                    .is_method_template(True).handle(child)

        if function_template is None:
            return
        self.header.header_add_template_function(function_template)
        self.add_function_template(function_template)
        self.identifier_map[function_template.scoped_id] = function_template.usr
        self.usr_map[function_template.usr] = function_template
        self.all_objects.append(function_template)
        return 

    def create_clang_child_object(self, node: cindex.Cursor) -> 'ParseObject':
        cpo_class = self.get_child_type(node)
        tparents = self.template_parents if not self.is_template else [*self.template_parents,
                self.template_ref]
        return cpo_class(node, self.force_parse).add_template_parents(tparents)\
                .set_header(self.header).set_scope(self).handle(node)


from clang import cindex, enumerations
import os
import typing
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser


@cmm.default_code_model(cindex.CursorKind.NAMESPACE)
class NamespaceObject(ParseObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)

        if not node:
            self["displayname"] = "GlobalNamespace"
            self["id"] = "GlobalNamespace"
            self["scoped_id"] = "GlobalNamespace"
            self["scoped_displayname"] = "GlobalNamespace"
            self["usr"] = "GlobalNamespace"
            self["scope"] = None
            self["kind"] = "NAMESPACE"

        self["header"] = None

        if not self["scope"]:
            self.set_scope(self)

        self.info["identifier_map"] = {}
        self.info["usr_map"] = {}
        self.info["all_objects"] = []

        self.info["namespaces"] = {}
        self.info["class_templates"] = {}
        self.info["partial_specializations"] = {}
        self.info["function_templates"] = {}
        self.info["typedefs"] = {}
        self.info["classes"] = {}
        self.info["structs"] = {}
        self.info["unions"] = {}
        self.info["functions"] = {}
        self.info["enumerations"] = {}
        self.info["namespace_aliases"] = {}
        self.info["type_aliases"] = {}
        self.info["template_aliases"] = {}
        self.info["using_directives"] = {}
        self.info["using_declarations"] = {}
        self.info["variables"] = {}
        self.info["exported_constants"] = {}
        self.info["is_class"] = False
        self.info["is_namespace"] = True
        self.info["is_union"] = False
        if node is not None:
            self.determine_scope_name(node)

        self.active_namespaces.append(self["scoped_id"])

        return

    def add_exported_const(self, const: "ParseObject") -> None:
        if const is None:
            return
        self["exported_constants"][const["displayname"]] = const
        return

    def add_namespace(self, ns: "NamespaceObject") -> None:
        if ns is None:
            return
        self["namespaces"][ns["displayname"]] = ns
        return

    def add_class_template(self, ct: "TemplateObject") -> None:
        if ct is None:
            return
        self["class_templates"][ct["displayname"]] = ct
        return

    def add_partial_specialization(self, part: "PartialSpecializationObject") -> None:
        if part is None:
            return
        self["partial_specializations"][part["displayname"]] = part
        return

    def add_function_template(self, ft: "TemplateObject") -> None:
        if ft is None:
            return
        self["function_templates"][ft["displayname"]] = ft
        return

    def add_typedef(self, td: "TypeDefObject") -> None:
        if td is None:
            return
        self["typedefs"][td["displayname"]] = td
        return

    def add_class(self, cls: "ClassObject") -> None:
        if cls is None:
            return
        self["classes"][cls["displayname"]] = cls
        return

    def add_struct(self, struct: "ClassObject") -> None:
        if struct is None:
            return
        self["structs"][struct["displayname"]] = struct
        return

    def add_union(self, union: "UnionObject") -> None:
        if union is None:
            return
        self["unions"][union["displayname"]] = union
        return

    def add_function(self, func: "FunctionObject") -> None:
        if func is None:
            return
        self["functions"][func["displayname"]] = func
        return

    def add_enumeration(self, enum: "EnumObject") -> None:
        if enum is None:
            return
        self["enumerations"][enum["displayname"]] = enum
        return

    def add_namespace_alias(self, ns_alias: "NamespaceAliasObject") -> None:
        if ns_alias is None:
            return
        self["namespace_aliases"][ns_alias["displayname"]] = ns_alias
        return

    def add_type_alias(self, t_alias: "TypeAliasObject") -> None:
        if t_alias is None:
            return
        self["type_aliases"][t_alias["displayname"]] = t_alias
        return

    def add_type_alias_template(self, tt_alias: "TemplateTypeAliasObject") -> None:
        if tt_alias is None:
            return
        self["template_aliases"][tt_alias["displayname"]] = tt_alias
        return

    def add_using_directive(self, u_dir: "UsingNamespaceObject") -> None:
        if u_dir is None:
            return
        self["using_directives"][u_dir["displayname"]] = u_dir
        self.active_namespaces = u_dir["using_namespace"]
        return

    def add_using_decl(self, u_decl: "UsingDeclarationObject") -> None:
        if u_decl is None:
            return
        self["using_declarations"][u_decl["displayname"]] = u_decl
        self.active_using_directives[u_decl["type_name"]] = u_decl["using_type"]
        return

    def add_variable(self, var: "VariableObject") -> None:
        if var is None:
            return
        self["variables"][var["displayname"]] = var
        return

    def add_object(self, add_method, node: cindex.Cursor) -> None:
        obj = self.create_clang_child_object(node)
        if obj.no_decl:
            return None
        if obj is None:
            return None
        add_method(obj)
        self["identifier_map"][obj["scoped_displayname"]] = obj["usr"]
        self["usr_map"][obj["usr"]] = obj
        self["all_objects"].append(obj)
        return obj

    def process_child(self, child: cindex.Cursor) -> typing.Optional["ParseObject"]:

        tparents = (
            self["template_parents"]
            if not self["is_template"]
            else [*self["template_parents"], self["template_ref"]]
        )

        if child.kind == cindex.CursorKind.NAMESPACE:
            return self.add_object(self.add_namespace, child)

        if child.kind == cindex.CursorKind.CLASS_TEMPLATE:

            actually_method = cindex.CursorKind.PARM_DECL in [
                x.kind for x in child.get_children()
            ]
            if actually_method:
                return self.handle_function_template(child)
            
            header_use = parser.get_header(child.location.file.name)
            cls_temp_obj = self.get_child_type(child)
            class_template = (
                cls_temp_obj(child, self["force_parse"])
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self)
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_parse_level(self["parse_level"])
                .do_handle(child)
            )
            if class_template.no_decl or not class_template.handle_object:
                return None
            self.add_class_template(class_template)
            self["identifier_map"][
                class_template["scoped_displayname"]
            ] = class_template["usr"]
            self["usr_map"][class_template["usr"]] = class_template
            self["all_objects"].append(class_template)
            return class_template

        if child.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:

            cls_temp_spec = self.get_child_type(child)

            header_use = parser.get_header(child.location.file.name)
            cls_template_spec = (
                cls_temp_spec(child, self["force_parse"])
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self)
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_parse_level(self["parse_level"])
                .do_handle(child)
            )
            if cls_template_spec.no_decl or not cls_template_spec.handle_object:
                return None
            self.add_partial_specialization(cls_template_spec)
            self["identifier_map"][
                cls_template_spec["scoped_displayname"]
            ] = cls_template_spec["usr"]
            self["usr_map"][cls_template_spec["usr"]] = cls_template_spec
            self["all_objects"].append(cls_template_spec)
            return cls_template_spec

        if child.kind == cindex.CursorKind.TYPEDEF_DECL:

            # Catch C typdef struct
            if child.underlying_typedef_type.spelling.startswith("struct "):
                struct_object = self.create_clang_child_object(child)
                if struct_object.no_decl or not struct_object.handle_object:
                    return None
                self.add_struct(struct_object)
                self["identifier_map"][
                    struct_object["scoped_displayname"]
                ] = struct_object["usr"]
                self["usr_map"][struct_object["usr"]] = struct_object
                self["all_objects"].append(struct_object)
                return struct_object
            else:
                typedef = self.create_clang_child_object(child)
                if typedef.no_decl or not typedef.handle_object:
                    return None
                self.add_typedef(typedef)
                self["identifier_map"][typedef["scoped_displayname"]] = typedef[
                    "usr"
                ]
                self["usr_map"][typedef["usr"]] = typedef
                self["all_objects"].append(typedef)
                return typedef

        if (
            child.kind == cindex.CursorKind.CLASS_DECL
            or child.kind == cindex.CursorKind.STRUCT_DECL
        ):
            if child.kind == cindex.CursorKind.CLASS_DECL:
                return self.add_object(self.add_class, child)
            else:
                return self.add_object(self.add_struct, child)

        if child.kind == cindex.CursorKind.UNION_DECL:
            return self.add_object(self.add_union, child)

        if child.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            return self.handle_function_template(child)

        if child.kind == cindex.CursorKind.ENUM_DECL:
            return self.add_object(self.add_enumeration, child)

        if child.kind == cindex.CursorKind.FUNCTION_DECL:
            return self.add_object(self.add_function, child)

        if child.kind == cindex.CursorKind.VAR_DECL:
            return self.add_object(self.add_variable, child)

        if child.kind == cindex.CursorKind.NAMESPACE_ALIAS:
            return self.add_object(self.add_namespace_alias, child)

        if child.kind == cindex.CursorKind.TYPE_ALIAS_DECL:
            return self.add_object(self.add_type_alias, child)

        if child.kind == cindex.CursorKind.FIELD_DECL:
            return self.add_object(self.add_variable, child)

        if child.kind == cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL:
            temp_alias_obj = self.get_child_type(child)
            header_use = parser.get_header(child.location.file.name)
            alias_template = (
                temp_alias_obj(child)
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self)
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_parse_level(self["parse_level"])
                .do_handle(child)
            )
            if alias_template.no_decl or not alias_template.handle_object:
                return None
            self.add_type_alias_template(alias_template)
            self["identifier_map"][
                alias_template["scoped_displayname"]
            ] = alias_template["usr"]
            self["usr_map"][alias_template["usr"]] = alias_template
            self["all_objects"].append(alias_template)
            return alias_template

        if child.kind == cindex.CursorKind.USING_DIRECTIVE:
            return self.add_object(self.add_using_directive, child)

        if child.kind == cindex.CursorKind.USING_DECLARATION:
            return self.add_object(self.add_using_decl, child)

        return None

    @if_handle
    def handle(self, node: cindex.Cursor) -> "NamespaceObject":
        
        if not self["is_template"]:
            ParseObject.handle(self, node)
        
        children = []
        self.extend_children(node, children)
        for child in children:
            child_obj = self.process_child(child)
            if child_obj is not None:
                child_obj.handle(child)
        return self

    def handle_function_template(self, child: cindex.Cursor) -> None:
        tparents = (
            self["template_parents"]
            if not self["is_template"]
            else [*self["template_parents"], self["template_ref"]]
        )
        fn_temp_obj = self.get_child_type(child)
        function_template = None
        header_use = parser.get_header(child.location.file.name)
        if not self["is_class"]:
            function_template = (
                fn_temp_obj(child, self["force_parse"])
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self)
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_parse_level(self["parse_level"])
                .is_function_template(True)
                .do_handle(child)
            )
        else:
            function_template = (
                fn_temp_obj(child, self["force_parse"])
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self)
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_parse_level(self["parse_level"])
                .is_method_template(True)
                .do_handle(child)
            )

        if function_template is None:
            return None
        if function_template.no_decl or not function_template.handle_object:
            return None
        self["identifier_map"][
            function_template["scoped_displayname"]
        ] = function_template["usr"]
        self["usr_map"][function_template["usr"]] = function_template
        self["all_objects"].append(function_template)
        return function_template

    def create_clang_child_object(self, node: cindex.Cursor) -> "ParseObject":
        cpo_class = self.get_child_type(node)
        tparents = (
            self["template_parents"]
            if not self["is_template"]
            else [*self["template_parents"], self["template_ref"]]
        )
        header_use = parser.get_header(node.location.file.name)
        scope_use = self["scope"] if self["export_to_scope"] else self
        return (
            cpo_class(node, self["force_parse"])
            .add_template_parents(tparents)
            .set_header(header_use)
            .set_scope(scope_use)
            .add_active_namespaces(self.active_namespaces)
            .add_active_directives(self.active_using_directives)
            .set_parse_level(self["parse_level"])
            .do_handle(node)
        )

from clang import cindex, enumerations
import typing
import regex
import copy
import pdb

from ..__config__ import ccmodel_config as ccm_cfg
from .types import (
    DependencyType,
    access_spec
)
from .decorators import if_handle, append_cpo
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser


class ParseObject(object):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):

        if node is not None:
            node.export_to_scope = False

        self.info = {}
        self.info["access_specifier"] = (
            node.access_specifier.name if node is not None else ""
        )
        self.info["linkage"] = node.linkage.name if node else ""
        self.info["kind"] = node.kind.name if node is not None else ""
        self.info["id"] = node.spelling if node else ""
        self.info["canonical_type"] = (
            node.canonical.type.spelling if node is not None else ""
        )
        self.info["type"] = node.type.spelling if node is not None else ""
        self.info["type"] = self["type"].replace(" >", ">")
        self.info["usr"] = node.get_usr() if node is not None else ""
        self.info["displayname"] = node.displayname if node else ""
        self.info["line_number"] = node.location.line if node else 0
        self.info["exclude_names"] = []
        self.info["header"] = None
        self.info["is_definition"] = node.is_definition() if node is not None else True
        self.info["definition"] = self
        self.info["hash"] = node.hash if node is not None else ""
        self.info["all_objects"] = []
        self.info["parse_id"] = None
        self.info["scope"] = None
        self.info["dependencies"] = []
        self.info["rules"] = []
        self.info["brief"] = None
        self.info["force_parse"] = force
        self.info["template_parents"] = []
        self.info["is_template"] = False
        self.info["is_namespace"] = False
        self.info["is_anonymous"] = False
        self.info["is_fparam"] = False
        self.info["is_function"] = False
        self.info["export_to_scope"] = False
        self.info["scope_name"] = ""
        self.info["scopedisp_name"] = ""
        self.info["scoped_id"] = ""
        self.info["scoped_displayname"] = ""
        self.info["storage_class"] = node.storage_class.name if node else ""
        self.info["unresolved_dep_usrs"] = []
        self.info["inherited"] = False
        self.info["parse_level"] = "PRIVATE"

        self.active_namespaces = []
        self.active_using_directives = {}

        self.handle_object = False
        self.force_search = False
        self.template_params_replaced = False
        self.is_handled = False
        self.no_decl = node.kind == cindex.CursorKind.NO_DECL_FOUND if node else False

        return

    def set_parse_level(self, plevel: str) -> "ParseObject":
        self["parse_level"] = plevel
        return self

    def add_active_namespaces(self, nss: typing.List[str]) -> "ParseObject":
        self.active_namespaces.extend([x for x in nss if x != "GlobalNamespace"])
        return self

    def add_active_directives(self, ad_dict: typing.Dict) -> "ParseObject":
        for key, val in ad_dict.items():
            self.active_using_directives[key] = val
        return self

    def __deepcopy__(self, memo) -> "ParseObject":
        new_po = self.__class__()
        new_po.__dict__.update(self.__dict__.copy())
        new_po.info = self.info.copy()

        del new_po.info["template_parents"]
        new_po.info["template_parents"] = []
        del new_po.info["all_objects"]
        new_po.info["all_objects"] = []

        for x in self["template_parents"]:
            tp = copy.deepcopy(x, memo)
            new_po["template_parents"].append(tp)
        for x in self["all_objects"]:
            ao = copy.deepcopy(x, memo)
            new_po["all_objects"].append(ao)

        return new_po

    def __getitem__(self, item: str):
        return self.info[item]

    def __setitem__(self, key: str, val):
        self.info[key] = val
        return

    def extend_children(
        self, node: "cindex.Cursor", ext_array: typing.List["cindex.Cursor"]
    ) -> None:
        children = node.get_children()
        for child in children:
            if child.kind == cindex.CursorKind.UNEXPOSED_DECL:
                self.extend_children(child, ext_array)
                continue
            ext_array.append(child)
        return

    def add_template_parents(
        self, tparents: typing.List["TemplateObject"]
    ) -> "ParseObject":
        self["template_parents"].extend(tparents)
        return self

    def determine_scope_name(self, node: cindex.Cursor) -> None:
        self["scope_name"] = ""
        scope_parts = []
        scopedisp_parts = []
        if (
            node is not None
            and node.kind == cindex.CursorKind.NAMESPACE
            and self.get_name() == ""
        ):
            scope_parts.append("$")
            scopedisp_parts.append("$")
            self["is_anonymous"] = True
        elif self.get_name() == "" and (
            node.kind == cindex.CursorKind.CLASS_DECL
            or node.kind == cindex.CursorKind.STRUCT_DECL
            or node.kind == cindex.CursorKind.UNION_DECL
        ):
            self["is_anonymous"] = True
            self["export_to_scope"] = True
            node.export_to_scope = True
        elif self.get_name() == "":
            self["is_anonymous"] = True
        if node is not None and node.semantic_parent is not None:
            parent = node.semantic_parent
            if "export_to_scope" not in dir(parent):
                if parent.spelling == "" and (
                    parent.kind == cindex.CursorKind.CLASS_DECL
                    or parent.kind == cindex.CursorKind.STRUCT_DECL
                    or parent.kind == cindex.CursorKind.UNION_DECL
                ):
                    parent.export_to_scope = True
                elif (
                    parent.kind == cindex.CursorKind.ENUM_DECL
                    and not parent.is_scoped_enum()
                ):
                    parent.export_to_scope = True
                else:
                    parent.export_to_scope = False
            while parent.kind is not cindex.CursorKind.TRANSLATION_UNIT:
                name_use = ""
                namedisp_use = ""
                if parent.kind is cindex.CursorKind.NAMESPACE and parent.spelling == "":
                    name_use = "$"
                    namedisp_use = "$"
                elif parent.spelling == "" and parent.export_to_scope:
                    if (
                        parent.semantic_parent.kind
                        is not cindex.CursorKind.TRANSLATION_UNIT
                    ):
                        name_use = parent.semantic_parent.spelling
                        namedisp_use = parent.semantic_parent.displayname
                elif (
                    node.semantic_parent.kind is cindex.CursorKind.ENUM_DECL
                    and node.semantic_parent.export_to_scope
                ):
                    if (
                        parent.semantic_parent.kind
                        is not cindex.CursorKind.TRANSLATION_UNIT
                    ):
                        name_use = parent.semantic_parent.spelling
                        namedisp_use = parent.semantic_parent.displayname
                else:
                    name_use = parent.spelling
                    namedisp_use = parent.displayname
                scope_parts.append(name_use)
                scopedisp_parts.append(namedisp_use)
                if (
                    not parent.export_to_scope
                    or parent.semantic_parent.kind == cindex.CursorKind.TRANSLATION_UNIT
                ):
                    parent = parent.semantic_parent
                    parent.export_to_scope = False
                elif parent.semantic_parent.semantic_parent is not None:
                    parent = parent.semantic_parent.semantic_parent
                    parent.export_to_scope = False
            scope_parts.reverse()
            scopedisp_parts.reverse()
            self["scope_name"] = "::".join(scope_parts)
            self["scopedisp_name"] = "::".join(scopedisp_parts)
        self["scoped_id"] = (
            "::".join([self["scope_name"], self["id"]])
            if self["scope_name"] != ""
            else self["id"]
        )
        self["scoped_displayname"] = (
            "::".join([self["scopedisp_name"], self["displayname"]])
            if self["scope_name"] != ""
            else self["displayname"]
        )

        if self["scoped_id"] == "GlobalNamespace":
            self["scoped_id"] = ""

        self["scope_name"] = self["scope_name"].replace("$", "")
        self["scoped_id"] = self["scoped_id"].replace("$", "")
        self["scoped_displayname"] = self["scoped_displayname"].replace("$", "")

        return

    def search_objects_by_name(
        self, search_str: str
    ) -> typing.Union["ParseObject", None]:

        for obj in self["all_objects"]:

            found_obj = obj.search_objects_by_name(search_str)
            if found_obj:
                return found_obj

            if obj.get_name() == search_str:
                return obj

        return None

    @property
    def object_logger(self):
        return self["header"].header_logger.bind(logs_parses=True)

    @property
    def dependency_logger(self):
        return self["header"].header_logger.bind(logs_object_deps=True)

    def set_header(self, header: "HeaderObject") -> "ParseObject":
        self["header"] = header
        return self

    def add_exclude_name(self, ex_name: str) -> None:
        self["exclude_names"].append(ex_name)
        return

    def set_scope(self, scope: "ParseObject") -> "ParseObject":
        self["scope"] = scope
        return self

    @append_cpo
    def handle(self, node: cindex.Cursor) -> "ParseObject":
        self["header"].register_object(self)
        if not self["is_definition"]:
            self["definition"] = self["header"].get_usr(node.referenced.get_usr())
        return self

    def get_name(self) -> str:
        return self["id"]

    def process_child(self, child: cindex.Cursor) -> None:
        return None

    def children(
        self, nodes: typing.List[cindex.Cursor], kind: cindex.CursorKind
    ) -> typing.List[cindex.Cursor]:
        return [x for x in nodes if x.kind == kind]

    def do_handle(self, node: cindex.Cursor) -> bool:
        if node.kind == cindex.CursorKind.NO_DECL_FOUND:
            return False
        in_unit = self.object_in_unit(node)
        parse_also = (
                self["scoped_id"] in parser.include_names or
                self["scoped_id"].startswith(tuple(parser.include_names)[-1])
                )
        pa_found = (
                self["scoped_id"] if self["scoped_id"] in parser.include_names else
                tuple(parser.include_names)[-1]
                )
        if parse_also:
            p_also = parser.include_names[pa_found]
            self["parse_level"] = p_also["access_specifier"]
            self.force_search = p_also["force_search"]
            self["force_parse"] = p_also["force_parse"]
        allowed = (
            self.get_name() != ""
            or (self.get_name() == "" and self["export_to_scope"])
            or (self.get_name() == "" and node.kind == cindex.CursorKind.NAMESPACE)
            or parse_also
        )
        allowed &= (access_spec[node.access_specifier.name] >= access_spec[self["parse_level"]])
        self.handle_object = self["force_parse"] or (
            in_unit
            and self["id"] not in parser.get_excludes()
            and allowed
        )
        return self

    def object_in_unit(self, node: cindex.Cursor) -> bool:
        return (
            node.displayname == self["header"].header_file
            or node.location.file.name in parser.headers
        )

    def create_clang_child_object(self, node: cindex.Cursor) -> "ParseObject":
        cpo_class = self.get_child_type(node)
        tparents = (
            self["template_parents"]
            if not self["is_template"]
            else [*self["template_parents"], self["template_ref"]]
        )
        header_use = parser.get_header(node.location.file.name)
        return (
            cpo_class(node, self["force_parse"])
            .set_parse_level(self["parse_level"])
            .add_template_parents(tparents)
            .set_header(header_use)
            .set_scope(self["scope"])
            .add_active_namespaces(self.active_namespaces)
            .add_active_directives(self.active_using_directives)
            .do_handle(node)
        )

    def get_child_type(self, node: cindex.Cursor) -> typing.Type:
        using_name = (
            self["scoped_id"] + "::" + node.spelling
            if self["scoped_id"] != ""
            else (
                self["scope_name"] + "::" + node.spelling
                if self["scope_name"] != ""
                else node.spelling
            )
        )
        if using_name in cmm.object_code_models:
            return cmm.object_code_models[using_name]
        return cmm.default_code_models[node.kind]

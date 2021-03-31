from clang import cindex, enumerations
import typing
import pdb

import illuminate.__config__.illuminate_config as il_cfg
from illuminate.code_models.types import DependencyType
from illuminate.code_models.decorators import (if_handle,
        append_cpo)
import illuminate.rules.code_model_map as cmm

import re


python_var_pattern = re.compile("(^[a-zA-Z_][a-zA-Z0-9_\.]*)")

linkage_map = {
        cindex.LinkageKind.EXTERNAL: 'EXTERNAL',
        cindex.LinkageKind.INTERNAL: 'INTERNAL',
        cindex.LinkageKind.INVALID: 'INVALID',
        cindex.LinkageKind.NO_LINKAGE: 'NO_LINKAGE',
        cindex.LinkageKind.UNIQUE_EXTERNAL: 'UNIQUE_EXTERNAL'
}

class ParseObject(object):

    def __init__(self, node: typing.Union[cindex.Cursor, None], force_parse: bool = False):

        self.linkage = linkage_map[node.linkage] if node else 'EXTERNAL'
        self.kind = node.kind if node is not None else None
        self.id = node.spelling if node else ""
        self.type = None if node is None else (node.canonical if node.type != '' else None)
        self.usr = node.get_usr() if node is not None else None
        self.displayname = node.displayname if node else ""
        self.line_number = node.location.line if node else 0
        self.exclude_names = []
        self.header = None
        self.is_definition = node.is_definition() if node is not None else True
        self.definition = self
        self.hash = node.hash if node is not None else None
        self.all_objects = []
        self.parse_id = None
        self.scope = None
        self.dep_objs = []
        self.rules = []
        self.is_also = []
        self.brief = None
        self.force_parse = force_parse

        self.scope_name = ""
        scope_parts = []
        if node is not None:
            parent = node.semantic_parent
            while parent.kind is not cindex.CursorKind.TRANSLATION_UNIT:
                scope_parts.append(parent.spelling)
                parent = parent.semantic_parent
            scope_parts.reverse()
            self.scope_name = "::".join(scope_parts) if len(scope_parts) > 0 else ""
        self.qualified_id = "::".join([self.scope_name, self.id]) if self.scope_name != "" \
                else self.id
        if self.qualified_id == "GlobalNamespace":
            self.qualified_id = ""

        return

    def search_objects_by_name(self, search_str: str) -> typing.Union['ParseObject', None]:

        for obj in self.all_objects:

            found_obj = obj.search_objects_by_name(search_str)
            if found_obj:
                return found_obj

            if obj.get_name() == search_str:
                return obj

        return None

    @property
    def object_logger(self):
        return self.header.header_logger.bind(logs_parses=True)

    @property
    def dependency_logger(self):
        return self.header.header_logger.bind(logs_object_deps=True)

    def set_header(self, header: 'HeaderObject') -> 'ParseObject':
        self.header = header
        return self

    def add_exclude_name(self, ex_name: str) -> None:
        self.exclude_names.append(ex_name)
        return

    def set_scope(self, scope: 'ParseObject') -> 'ParseObject':
        self.scope = scope
        self.qualified_id = (self.scope.qualified_id + "::" + self.id).replace('GlobalNamespace::', '') \
                if self.scope and self.scope.qualified_id else self.id
        return self

    def handle(self, node: cindex.Cursor) -> 'ParseObject':
        self.header.register_object(self)
        if not self.is_definition:
            self.definition = self.header.get_usr(node.referenced.get_usr())
        return self

    def get_name(self) -> str:
        return self.id

    def set_linkage(self, language: int) -> None:
        self.linkage = language
        return

    def get_linkage(self) -> int:
        return self.linkage

    def get_scope(self) -> str:
        return self.scope.id

    def children(self, node: cindex.Cursor, kind: cindex.CursorKind) -> typing.List[cindex.Cursor]:
        return [x for x in node.get_children() if x.kind == kind and self.check_object_in_unit(x)]

    def do_handle(self, node: cindex.Cursor) -> bool:
        obj_in_or_force = self.force_parse or self.object_in_unit(node) 
        return obj_in_or_force and self.id not in self.header.parser.get_excludes() and \
            not self.header.in_registry(self.hash) and self.get_name() != "" or self.force_parse

    def object_in_unit(self, node: cindex.Cursor) -> bool:
        return node.displayname == self.header.header_file or \
                node.location.file.name in self.header.unit_headers

    def check_object_in_unit(self, node: cindex.Cursor) -> bool:
        return node.displayname == self.header.header_file or \
                node.location.file.name in self.header.unit_headers

    def create_clang_child_object(self, node: cindex.Cursor) -> 'ParseObject':
        cpo_class = self.get_child_type(node)
        return cpo_class(node, self.force_parse).set_header(self.header).set_scope(self).handle(node)

    def descendant_of_object(self, obj: 'ParseObject') -> bool:

        if obj.id == "GlobalNamespace":
            return True

        start_scope = self.scope
        while start_ns.get_name() != 'GlobalNamespace':
            if start_ns is ancestor:
                return True
            start_ns = start_ns.scope

        return False

    def get_child_type(self, node: cindex.Cursor) -> typing.Type:
        using_name = self.qualified_id + "::" + node.spelling if self.qualified_id \
                != "" else (self.scope_name + "::" + node.spelling if self.scope_name != "" \
                else node.spelling)
        if using_name in cmm.object_code_models:
            return cmm.object_code_models[using_name]
        return cmm.default_code_models[node.kind]



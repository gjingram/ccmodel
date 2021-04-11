from clang import cindex, enumerations
import typing
import regex
import pdb

from ..__config__ import ccmodel_config as ccm_cfg
from .types import DependencyType
from .decorators import (if_handle,
        append_cpo)
from ..rules import code_model_map as cmm

linkage_map = {
        cindex.LinkageKind.EXTERNAL: 'EXTERNAL',
        cindex.LinkageKind.INTERNAL: 'INTERNAL',
        cindex.LinkageKind.INVALID: 'INVALID',
        cindex.LinkageKind.NO_LINKAGE: 'NO_LINKAGE',
        cindex.LinkageKind.UNIQUE_EXTERNAL: 'UNIQUE_EXTERNAL'
}

template_targlist = r"(?P<match>(?P<t_name>(?::{2})?\w*(?::{2}~?\w*)*[^<])(?P<t_section>\s*<\s*(?P<t_arglist>.*)\s*>\s*))"
re_targlist = regex.compile(template_targlist)

def split_template_list(args_in: str) -> typing.List[str]:
    bracket_level = 0
    str_buffer = []
    out = []
    for char in args_in:
        if bracket_level == 0 and char == ",":
            out.append("".join(str_buffer).strip())
            str_buffer = []
            continue
        if char == "<":
            bracket_level += 1
        if char == ">":
            bracket_level -= 1
        str_buffer.append(char)
    out.append("".join(str_buffer).strip())
    return out

def replace_template_params(obj: 'ParseObject'):
    if len(obj.template_parents) == 0 or obj.template_params_replaced:
        return

    rparams = []
    for parent in obj.template_parents:
        rparams.extend([x.get_name() for x in parent.template_parameters])

    template_match = re_targlist.search(obj.scoped_displayname.replace(' ' ,''))
    if template_match is None:
        return
   
    template_list = split_template_list(template_match.group('t_arglist'))
    for rparam in rparams:
        for idx, param in enumerate(template_list):
            if param == rparam:
                template_list[idx] = "~"
                break
            if "type-parameter" in param:
                template_list[idx] = "~"
                break
    new_post = "<" + ", ".join(template_list) + ">"
    obj.scoped_displayname = obj.scoped_id.replace(' ', '').replace(template_match.group('t_section'), new_post)
    obj.template_params_replaced = True

    return

class ParseObject(object):

    def __init__(self, node: typing.Union[cindex.Cursor, None], force_parse: bool = False):

        self.linkage = linkage_map[node.linkage] if node else 'EXTERNAL'
        self.kind = node.kind if node is not None else None
        self.id = node.spelling if node else ""
        self.canonical_type = node.canonical.type.spelling if node is not None else ''
        self.type = node.type.spelling if node is not None else ''
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
        self.template_parents = []
        self.template_params_replaced = False
        self.is_template = False

        self.scope_name = ""
        self.scoped_id = ""
        self.scoped_displayname = ""

        self.determine_scope_name(node)

        return

    def add_template_parents(self, tparents: typing.List['TemplateObject']) -> 'ParseObject':
        self.template_parents.extend(tparents)
        return self

    def determine_scope_name(self, node: cindex.Cursor) -> None:
        self.scope_name = ""
        scope_parts = []
        if node is not None:
            parent = node.semantic_parent
            while parent.kind is not cindex.CursorKind.TRANSLATION_UNIT:
                scope_parts.append(parent.spelling)
                parent = parent.semantic_parent
            scope_parts.reverse()
            self.scope_name = "::".join(scope_parts) if len(scope_parts) > 0 else ""
        self.scoped_id = "::".join([self.scope_name, self.id]) if self.scope_name != "" \
                else self.id
        self.scoped_displayname = "::".join([self.scope_name, self.displayname]) if self.scope_name != "" \
                else self.displayname
        if self.scoped_id == "GlobalNamespace":
            self.scoped_id = ""

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
        return self

    @append_cpo
    def handle(self, node: cindex.Cursor) -> 'ParseObject':
        replace_template_params(self)
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
        tparents = self.template_parents if not self.is_template else [*self.template_parents,
                self.template_ref]
        return cpo_class(node, self.force_parse).add_template_parents(tparents)\
                .set_header(self.header).set_scope(self.scope).handle(node)

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
        using_name = self.scoped_id + "::" + node.spelling if self.scoped_id \
                != "" else (self.scope_name + "::" + node.spelling if self.scope_name != "" \
                else node.spelling)
        if using_name in cmm.object_code_models:
            return cmm.object_code_models[using_name]
        return cmm.default_code_models[node.kind]



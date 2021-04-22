from clang import cindex, enumerations
import typing
import os
import copy
import regex
import pdb

from ..__config__ import clang_config as ccm_cc
from ..__config__ import ccmodel_config as ccm_cfg
from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .namespace import NamespaceObject
from .class_object import ClassObject
from .union import UnionObject
from .variable import VariableObject
from .member import MemberObject
from .function import FunctionObject
from .function_param import FunctionParamObject
from .member_function import MemberFunctionObject
from .template import (TemplateObject,
        PartialSpecializationObject)
from .template_param import TemplateParamObject, re_param
from .enumeration import EnumObject, EnumConstDeclObject
from .comment_object import CommentObject
from .alias_objects import TypeDefObject, \
        TypeAliasObject, NamespaceAliasObject, TemplateAliasObject
from .directive_objects import UsingNamespaceObject, \
        UsingDeclarationObject
from ..utils import summary
from ..utils.code_utils import re_targlist
from ..rules import code_model_map as cmm

cindex = ccm_cc.clang.cindex
HeaderSummary = summary.HeaderSummary

@cmm.default_code_model("header")
class HeaderObject(object):

    
    def __init__(self, node: cindex.Cursor,
            header_file: str, parser: "illuminate.parsers.cpp_parse.ClangCppParse"):
        
        self.header_file = header_file
        self.directory = os.path.join(*header_file.split(os.sep)[:-1])
        self.base_namespace = NamespaceObject(None)
        self.unit_includes = []
        self.extern_includes = []
        self.comments = []
        self.parser = parser
        self.n_objs = 0
        self.summary = HeaderSummary()
        self.summary.file = self.header_file
        self.summary.path = self.directory
        self.get_last_modified_time()
        self.hash_registry = []

        self.header_add_fns = {
            "TYPEDEF_DECL": self.header_add_typedef,
            "TYPE_ALIAS_DECL": self.header_add_typedef,
            "NAMESPACE_ALIAS": self.header_add_namespace_alias,
            "TYPE_ALIAS_TEMPLATE_DECL": self.header_add_template_alias,
            "CLASS_DECL": self.header_add_class,
            "STRUCT_DECL": self.header_add_class,
            "USING_DIRECTIVE": self.header_add_using_namespace,
            "USING_DECLARATION": self.header_add_using_decl,
            "ENUM_DECL": self.header_add_enum,
            "FUNCTION_DECL": self.header_add_function,
            "NAMESPACE": self.header_add_namespace,
            "CLASS_TEMPLATE": self.header_add_template_class,
            "FUNCTION_TEMPLATE": self.header_add_template_function,
            "UNION_DECL": self.header_add_union,
            "VAR_DECL": self.header_add_variable,
            "PARM_DECL": self.header_add_fn_param,
            "ENUM_CONSTANT_DECL": self.header_add_enum_decl,
            "TEMPLATE_TEMPLATE_PARAMETER": self.header_add_template_template_param,
            "TEMPLATE_TYPE_PARAMETER": self.header_add_template_type_param,
            "TEMPLATE_NON_TYPE_PARAMETER": self.header_add_template_non_type_param,
            "FIELD_DECL": self.header_add_class_member,
            "CONSTRUCTOR": self.header_add_class_ctor,
            "DESTRUCTOR": self.header_add_class_dtor,
            "CONVERSION_FUNCTION": self.header_add_class_conversion,
            "CXX_METHOD": self.header_add_class_method,
            "CLASS_TEMPLATE_PARTIAL_SPECIALIZATION": self.header_add_partial_spec
            }

        self.template_specializations = {}


        return

    @property
    def header_logger(self):
        return ccm_cfg.logger.bind(log_parsed=ccm_cfg.log_parsed,
                log_object_deps=ccm_cfg.log_object_deps,
                header=self.header_file)

    def get_last_modified_time(self) -> None:
        try:
            self.summary.last_modified = os.path.getmtime(self.header_file)
        except:
            warnings.warn(f"Could not obtain last file modification time for \"{self.header_file}\".")
            self.summary.last_modified = 0
        return

    def in_registry(self, hash_in: int) -> bool:
        return hash_in in self.hash_registry

    def register_object(self, cpo: ParseObject) -> None:
        if not self.in_registry(cpo["hash"]):
            self.hash_registry.append(cpo["hash"])
            cpo["parse_id"] = self.n_objs
            self.n_objs += 1
        return

    def add_usr(self, obj: ParseObject) -> None:
        self.summary.identifier_map[obj.scoped_id] = obj.usr
        self.summary.usr_map[usr] = obj
        return

    def get_usr(self, usr: str) -> None:
        try:
            return self.summary.usr_map[usr]
        except KeyError:
            pass
        return None

    def header_extend_dep(self, dep_obj: 'ParseObject', obj: 'ParseObject') -> None:
        for dep in dep_obj.dependencies:
            obj.dependencies.append(dep.definition)
            self.header_extend_dep(dep, obj)
        return

    def header_get_dep(self, child: cindex.Cursor, po: ParseObject) -> 'ParseObject':
        ref_node = None
        if not child.is_definition():
            test_node = child.get_definition()
            ref_node = child if test_node is None else test_node
        else:
            ref_node = child

        dep_obj = None
        if ref_node == child:
            po_tmp = ParseObject(ref_node)
            match_template = re_targlist.match(po_tmp["displayname"])
            if match_template and "t_arglist" in match_template.groupdict() and \
                    match_template.groupdict()["t_arglist"] is not None:
                try_template = self.header_match_template_ref(
                        po_tmp["scoped_id"],
                        match_template.groupdict()["t_arglist"].replace(' ', '').split(','))
                if try_template is not None:
                    dep_obj = try_template
        if dep_obj is None:
            dep_obj = self.get_usr(ref_node.get_usr())
        if dep_obj is not None:
            po["dependencies"].append(dep_obj)
        else:
            dep_obj = self.header_add_object(self.base_namespace, ref_node)
            po["dependencies"].append(dep_obj)
        return dep_obj

    def header_match_template_ref(self, qual: str,
            params: typing.Tuple[str]) -> typing.Optional['TemplateObject']:

        if not qual in self.template_specializations:
            return None
        specializations = self.template_specializations[qual]
        possible_match_keys = []
        for spec_key in specializations.keys():
            if len(spec_key) == len(params):
                possible_match_keys.append(list(spec_key))
            elif len(params) > len(spec_key) and spec_key[-1].endswith("[#...]"):
                possible_match_keys.append(list(spec_key))
            elif len(params) < len(spec_key):
                start_list = copy.deepcopy(spec_key)
                default_or_variadic = True
                end_is_variadic = False
                for remain in spec_key[len(params):]:
                    default_type = re_param.search(remain).group('default')
                    default = default_type is not None and default_type != "#" and \
                            default_type != "#..."
                    variadic = remain == '[#...]'
                    default_or_variadic &= (default or variadic)
                if default_or_variadic:
                    possible_match_keys.append(spec_key)
        match_copies = copy.deepcopy(possible_match_keys)
        param_copy = list(copy.deepcopy(params))
        for pspec_idx, pspec_key in enumerate(match_copies):
            for param_idx, param in enumerate(param_copy):
                if param_idx < len(pspec_key):
                    if pspec_key[param_idx].endswith("#"):
                        continue
                    elif pspec_key[param_idx] == param:
                        continue
                    elif re_param.search(pspec_key[param_idx]).groupdict()["default"] is not None:
                        continue
                    elif param_idx == len(params) - 1:
                        for remain in pspec_key[param_idx:]:
                            default = re_param.search(remain).group('default')
                            if default is not None:
                                continue
                            elif remain.endswith('[#...]'):
                                continue
                            else:
                                possible_match_keys.pop(pspec_idx)
                                break
                        continue
                    else:
                        possible_match_keys.pop(pspec_idx)
                        break
                elif param_idx >= len(pspec_key) - 1 and pspec_key[-1] == "[#...]":
                    continue
                else:
                    possible_match_keys.pop(pspec_idx)
                    break 
        match = None
        min_pound = -1
        for pmatch in possible_match_keys:
            pound_cnt = 0
            for p in pmatch:
                if "#" in p:
                    pound_cnt += 1
            if min_pound < 0 or pound_cnt < min_pound:
                match = specializations[tuple(pmatch)]
                min_pound = pound_cnt
                if pmatch[-1].endswith('[#...]') and len(params) > len(pmatch):
                    min_pound += len(params) - len(pmatch) - 1

        inst_candidate = True
        for param in params:
            inst_candidate &= "#" not in param
        if inst_candidate:
            match = match.instantiate(params)
        return match

    def header_add_unknown(self, obj: 'ParseObject') -> None:
        self.summary.all_objects.append(obj)
        return

    def header_add_object(self, scope: 'ParseObject', node: cindex.Cursor) -> ParseObject:
        temp = self.get_usr(node.get_usr())
        if temp:
            return temp
        model = None
        add_fn = None
        try:
            model = cmm.default_code_models[node.kind]
            add_fn = self.header_add_fns[node.kind.name]
        except KeyError:
            model = ParseObject
            add_fn = self.header_add_unknown
        scope_use = self.base_namespace
        try:
            scope_use = self.get_usr(node.semantic_parent.get_usr())
        except:
            pass
        parent = node.semantic_parent
        tparents = []
        while parent is not None and parent.kind != cindex.CursorKind.TRANSLATION_UNIT:
            if parent.kind == cindex.CursorKind.FUNCTION_TEMPLATE or \
                    parent.kind == cindex.CursorKind.CLASS_TEMPLATE:
                try:
                    temp = self.get_usr(parent.get_usr())
                    tparents.append(temp)
                except KeyError:
                    pass
            parent = parent.semantic_parent
        obj = model(node, force=True).set_header(self).set_scope(scope_use)\
                .add_template_parents(tparents).handle(node)
        self.summary.add_obj_to_summary_maps(obj)
        return obj

    def header_add_class(self, _class: ClassObject) -> None:
        if not _class in self.summary.classes:
            self.summary.classes.append(_class)
        return

    def header_add_class_member(self, member: MemberObject) -> None:
        if not member in self.summary.class_members:
            self.summary.class_members.append(member)
        return

    def header_add_class_ctor(self, ctor: MemberFunctionObject) -> None:
        self.header_add_class_conversion(ctor)
        if not ctor in self.summary.class_ctors:
            self.summary.class_ctors.append(ctor)
        return

    def header_add_class_dtor(self, dtor: MemberFunctionObject) -> None:
        if not dtor in self.summary.class_dtors:
            self.summary.class_dtors.append(dtor)
        return

    def header_add_class_method(self, method: MemberFunctionObject) -> None:
        self.header_add_class_conversion(method)
        if not method in self.summary.class_methods:
            self.summary.class_methods.append(method)
        return

    def header_add_class_conversion(self, method: MemberFunctionObject) -> None:
        if method["is_conversion"] or method["is_converting_ctor"]:
            if not method in self.summary.class_conversions:
                self.summary.class_conversions.append(method)
        return

    def header_add_using_namespace(self, uns: UsingNamespaceObject) -> None:
        if not uns in self.summary.using:
            self.summary.using.append(uns)
        return

    def header_add_using_decl(self, udecl: UsingDeclarationObject) -> None:
        if not udecl in self.summary.using:
            self.summary.using.append(udecl)
        return

    def header_add_namespace(self, namespace: NamespaceObject) -> None:
        if not namespace in self.summary.namespaces:
            self.summary.namespaces.append(namespace)
        return

    def header_add_union(self, union: UnionObject) -> None:
        if not union in self.summary.unions:
            self.summary.unions.append(union)
        return

    def header_add_variable(self, var: VariableObject) -> None:
        if not var in self.summary.variables:
            self.summary.variables.append(var)
        return

    def header_add_function(self, func: FunctionObject) -> None:
        if not func in self.summary.functions:
            self.summary.functions.append(func)
        return

    def header_add_template_class(self, temp: TemplateObject) -> None:
        if not temp in self.summary.template_classes:
            self.summary.template_classes.append(temp)
        return

    def header_add_template_function(self, tfunc: TemplateObject) -> None:
        if not tfunc in self.summary.template_functions:
            self.summary.template_functions.append(tfunc)
        return

    def header_add_template_template_param(self, ttparam: TemplateParamObject) -> None:
        if not ttparam in self.summary.template_template_params:
            self.summary.template_template_params.append(ttparam)
        return

    def header_add_template_type_param(self, ttparam: TemplateParamObject) -> None:
        if not ttparam in self.summary.template_type_params:
            self.summary.template_type_params.append(ttparam)
        return

    def header_add_template_non_type_param(self, tntparam: TemplateParamObject) -> None:
        if not tntparam in self.summary.template_non_type_params:
            self.summary.template_non_type_params.append(tntparam)
        return

    def header_add_partial_spec(self, partial: TemplateObject) -> None:
        if not partial in self.summary.partial_specializations:
            self.summary.partial_specializations.append(partial)
        return

    def header_add_fn_param(self, param: FunctionParamObject) -> None:
        if not param in self.summary.function_params:
            self.summary.function_params.append(param)
        return

    def get_namespace_by_scoped_id(self, ns_id: str) -> typing.Union['NamespaceObject', None]:
        for ns in self.summary.namespaces:
            if ns.scoped_id == ns_id:
                return ns
        return None

    def header_add_typedef(self, tdef: TypeDefObject) -> None:
        if not tdef in self.summary.typedefs:
            self.summary.typedefs.append(tdef)
        return

    def header_add_template_alias(self, t_alias: TemplateAliasObject) -> None:
        if not t_alias in self.summary.template_aliases:
            self.summary.template_aliases.append(t_alias)
        return

    def header_add_namespace_alias(self, nalias: NamespaceAliasObject) -> None:
        if not nalias in self.summary.namespace_aliases:
            self.summary.namespace_aliases.append(nalias)
        return

    def header_add_enum(self, enum: EnumObject) -> None:
        if not enum in self.summary.enumerations:
            self.summary.enumerations.append(enum)
        return

    def header_add_enum_decl(self, decl: EnumConstDeclObject) -> None:
        if not decl in self.summary.enum_fields:
            self.summary.enum_fields.append(decl)
        return

    def get_header_file(self) -> str:
        return self.header_file

    def handle_includes(self, parse: cindex.TranslationUnit) -> None:

        for file_include in parse.get_includes():
            include_name = str(file_include.include.name)
            if not include_name in self.parser.headers:
                self.unit_includes.append(include_name)
            else:
                self.extern_includes.append(include_name)
        return

    def handle(self, node: cindex.Cursor) -> 'HeaderObject':

        self.summary.comments[self.header_file] = []

        # Get all comments in the file first
        for tok in node.get_tokens():
            if tok.kind == cindex.TokenKind.COMMENT:
                self.summary.comments[self.header_file].append(CommentObject(tok))

        self.base_namespace.set_header(self)
        self.base_namespace.handle(node)

        return self

    def _handleDiagnostic(self, diag) -> bool:

        diagMsg = "{}\nline {} column {}\n{}".format(str(diag.location.file),
                                                     diag.location.line,
                                                     diag.location.column,
                                                     diag.spelling)

        if diag.severity == cindex.Diagnostic.Warning:
            raise RuntimeWarning(diagMsg)

        if diag.severity >= cindex.Diagnostic.Error:
            raise RuntimeError(diagMsg)

        return

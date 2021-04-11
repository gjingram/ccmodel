from clang import cindex, enumerations
import typing
import os
import copy
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
from .template import TemplateObject
from .template_param import TemplateParamObject, re_param
from .enumeration import EnumObject, EnumConstDeclObject
from .comment_object import CommentObject
from .alias_objects import TypeDefObject, \
        TypeAliasObject, NamespaceAliasObject, TemplateAliasObject
from .directive_objects import UsingNamespaceObject, \
        UsingDeclarationObject
from ..utils import summary
from ..rules import code_model_map as cmm

cindex = ccm_cc.clang.cindex
HeaderSummary = summary.HeaderSummary

@cmm.default_code_model("header")
class HeaderObject(object):

    
    def __init__(self, node: cindex.Cursor, header_file: str, parser: "illuminate.parsers.cpp_parse.ClangCppParse"):
        
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

        self.header_add_namespace(self.base_namespace)

        self.hash_registry = []

        self.header_add_fns = {
            cindex.CursorKind.TYPEDEF_DECL: self.header_add_typedef,
            cindex.CursorKind.TYPE_ALIAS_DECL: self.header_add_typedef,
            cindex.CursorKind.NAMESPACE_ALIAS: self.header_add_namespace_alias,
            cindex.CursorKind.TYPE_ALIAS_TEMPLATE_DECL: self.header_add_template_alias,
            cindex.CursorKind.CLASS_DECL: self.header_add_class,
            cindex.CursorKind.STRUCT_DECL: self.header_add_class,
            cindex.CursorKind.USING_DIRECTIVE: self.header_add_using_namespace,
            cindex.CursorKind.USING_DECLARATION: self.header_add_using_decl,
            cindex.CursorKind.ENUM_DECL: self.header_add_enum,
            cindex.CursorKind.FUNCTION_DECL: self.header_add_function,
            cindex.CursorKind.NAMESPACE: self.header_add_namespace,
            cindex.CursorKind.CLASS_TEMPLATE: self.header_add_template_class,
            cindex.CursorKind.FUNCTION_TEMPLATE: self.header_add_template_function,
            cindex.CursorKind.UNION_DECL: self.header_add_union,
            cindex.CursorKind.VAR_DECL: self.header_add_variable,
            cindex.CursorKind.PARM_DECL: self.header_add_fn_param,
            cindex.CursorKind.ENUM_CONSTANT_DECL: self.header_add_enum_decl,
            cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER: self.header_add_template_template_param,
            cindex.CursorKind.TEMPLATE_TYPE_PARAMETER: self.header_add_template_type_param,
            cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER: self.header_add_template_non_type_param,
            cindex.CursorKind.FIELD_DECL: self.header_add_class_member,
            cindex.CursorKind.CONSTRUCTOR: self.header_add_class_ctor,
            cindex.CursorKind.DESTRUCTOR: self.header_add_class_dtor,
            cindex.CursorKind.CXX_METHOD: self.header_add_class_method,
            cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION: self.header_add_partial_spec
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
        if not self.in_registry(cpo.hash):
            self.hash_registry.append(cpo.hash)
            cpo.parse_id = self.n_objs
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
        for dep in dep_obj.dep_objs:
            obj.dep_objs.append(dep.definition)
            self.header_extend_dep(dep, obj)
        return

    def header_get_dep(self, child: cindex.Cursor, po: ParseObject) -> 'ParseObject':
        ref_node = None
        if not child.is_definition():
            test_node = child.get_definition()
            ref_node = child if test_node is None else test_node
        else:
            ref_node = child
        dep_obj = self.get_usr(ref_node.get_usr())

        if dep_obj is not None:
            po.dep_objs.append(dep_obj)
        else:
            po.dep_objs.append(self.header_add_object(self.base_namespace, ref_node))
        return dep_obj

    def header_match_template_ref(self, qual: str, params: typing.Tuple[str]) -> typing.Optional['TemplateObject']:
        if not qual in self.template_specializations:
            return None
        specializations = self.template_specializations[qual]
        possible_match_keys = []
        for spec_key in specializations.keys():
            if len(spec_key) == len(params):
                possible_match_keys.append(list(spec_key))
            elif len(params) > len(spec_key) and spec_key[-1].endswith("[~...]"):
                possible_match_keys.append(list(spec_key))
            elif len(params) < len(spec_key):
                start_list = copy.deepcopy(spec_key)
                default_or_variadic = True
                end_is_variadic = False
                for remain in spec_key[len(params):]:
                    default_val = re.param.search(remain).group('default')
                    default = default_val is not None and default_val != "~" and \
                            default_val != "~..."
                    variadic = remain.endswith('[~...]')
                    default_or_variadic &= default or variadic
                if default_or_variadic:
                    possible_match_keys.append(spec_key)
        match_copies = copy.deepcopy(possible_match_keys)
        param_copy = list(copy.deepcopy(params))
        for pspec_idx, pspec_key in enumerate(match_copies):
            for param_idx, param in enumerate(param_copy):
                if param_idx < len(pspec_key):
                    if pspec_key[param_idx] == "~":
                        continue
                    elif pspec_key[param_idx] == param:
                        continue
                    elif re_param.search(param).group('default') == pspec_key[param_idx]:
                        continue
                    elif param_idx == len(params) - 1:
                        for remain in pspec_key[param_idx:]:
                            default = re.param.search(remain).group('default')
                            if default is not None:
                                continue
                            elif remain.endswith('...'):
                                continue
                            else:
                                possible_match_keys.pop(pspec_idx)
                                break
                        continue
                    else:
                        possible_match_keys.pop(pspec_idx)
                        break
                elif param_idx >= len(pspec_key) - 1 and pspec_key[-1].endswith('...'):
                    continue
                else:
                    possible_match_keys.pop(pspec_idx)
                    break 
        match = None
        min_tildes = -1
        for pmatch in possible_match_keys:
            if min_tildes < 0 or pmatch.count("~") < min_tildes:
                match = specializations[tuple(pmatch)]
                min_tildes = pmatch.count("~")
                if pmatch[-1].endswith('...') and len(params) > len(pmatch):
                    min_tiles += len(params) - len(pmatch) - 1
        return match

    def header_add_object(self, scope: 'ParseObject', node: cindex.Cursor) -> ParseObject:
        model = cmm.default_code_models[node.kind]
        obj = model(node, True).set_header(self).handle(node)
        self.header_add_fns[node.kind](obj)
        self.summary.usr_map[obj.usr] = obj
        self.summary.identifier_map[obj.scoped_id] = obj.usr
        return obj

    def header_add_class(self, _class: ClassObject) -> None:
        self.summary.all_objects.append(_class)
        self.summary.classes.append(_class)
        return

    def header_add_class_member(self, member: MemberObject) -> None:
        self.summary.all_objects.append(member)
        self.summary.class_members.append(member)
        return

    def header_add_class_ctor(self, ctor: MemberFunctionObject) -> None:
        self.header_add_class_conversion(ctor)
        self.summary.all_objects.append(ctor)
        self.summary.class_ctors.append(ctor)
        return

    def header_add_class_dtor(self, dtor: MemberFunctionObject) -> None:
        self.summary.all_objects.append(dtor)
        self.summary.class_dtors.append(dtor)
        return

    def header_add_class_method(self, method: MemberFunctionObject) -> None:
        self.header_add_class_conversion(method)
        self.summary.all_objects.append(method)
        self.summary.class_methods.append(method)
        return

    def header_add_class_conversion(self, method: MemberFunctionObject) -> None:
        if method.is_conversion or method.converting_ctor:
            self.summary.class_conversions.append(method)
        return

    def header_add_using_namespace(self, uns: UsingNamespaceObject) -> None:
        self.summary.all_objects.append(uns)
        self.summary.using.append(uns)
        return

    def header_add_using_decl(self, udecl: UsingDeclarationObject) -> None:
        self.summary.all_objects.append(udecl)
        self.summary.using.append(udecl)
        return

    def header_add_namespace(self, namespace: NamespaceObject) -> None:
        self.summary.all_objects.append(namespace)
        self.summary.namespaces.append(namespace)
        return

    def header_add_union(self, union: UnionObject) -> None:
        self.summary.all_objects.append(union)
        self.summary.unions.append(union)
        return

    def header_add_variable(self, var: VariableObject) -> None:
        self.summary.all_objects.append(var)
        self.summary.variables.append(var)
        return

    def header_add_function(self, func: FunctionObject) -> None:
        self.summary.all_objects.append(func)
        self.summary.functions.append(func)
        return

    def header_add_template_class(self, temp: TemplateObject) -> None:
        self.summary.all_objects.append(temp)
        self.summary.template_classes.append(temp)
        return

    def header_add_template_function(self, tfunc: TemplateObject) -> None:
        self.summary.all_objects.append(tfunc)
        self.summary.template_functions.append(tfunc)
        return

    def header_add_template_template_param(self, ttparam: TemplateParamObject) -> None:
        self.summary.all_objects.append(ttparam)
        self.summary.template_template_params.append(ttparam)
        return

    def header_add_template_type_param(self, ttparam: TemplateParamObject) -> None:
        self.summary.all_objects.append(ttparam)
        self.summary.template_type_params.append(ttparam)
        return

    def header_add_template_non_type_param(self, tntparam: TemplateParamObject) -> None:
        self.summary.all_objects.append(tntparam)
        self.summary.template_non_type_params.append(tntparam)
        return

    def header_add_partial_spec(self, partial: TemplateObject) -> None:
        self.summary.all_objects.append(partial)
        self.summary.partial_specializations.append(partial)
        return

    def header_add_fn_param(self, param: FunctionParamObject) -> None:
        self.summary.all_objects.append(param)
        self.summary.function_params.append(param)
        return

    def get_namespace_by_scoped_id(self, ns_id: str) -> typing.Union['NamespaceObject', None]:
        for ns in self.summary.namespaces:
            if ns.scoped_id == ns_id:
                return ns
        return None

    def header_add_typedef(self, tdef: TypeDefObject) -> None:
        self.summary.all_objects.append(tdef)
        self.summary.typedefs.append(tdef)
        return

    def header_add_template_alias(self, t_alias: TemplateAliasObject) -> None:
        self.summary.all_objects.append(t_alias)
        self.summary.template_aliases.append(t_alias)
        return

    def header_add_namespace_alias(self, nalias: NamespaceAliasObject) -> None:
        self.summary.all_objects.append(nalias)
        self.summary.namespace_aliases.append(nalias)
        return

    def header_add_enum(self, enum: EnumObject) -> None:
        self.summary.all_objects.append(enum)
        self.summary.enumerations.append(enum)
        return

    def header_add_enum_decl(self, decl: EnumConstDeclObject) -> None:
        self.summary.all_objects.append(decl)
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

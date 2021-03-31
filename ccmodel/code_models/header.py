from clang import enumerations
import typing
import os
import pdb

import illuminate.__config__.clang_config as ilcc
import illuminate.__config__.illuminate_config as il_cfg
from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
from illuminate.code_models.namespace import NamespaceObject
from illuminate.code_models.class_object import ClassObject
from illuminate.code_models.union import UnionObject
from illuminate.code_models.variable import VariableObject
from illuminate.code_models.function import FunctionObject
from illuminate.code_models.template import TemplateObject
from illuminate.code_models.enumeration import EnumObject
from illuminate.code_models.comment_object import CommentObject
from illuminate.code_models.alias_objects import TypeDefObject, \
        TypeAliasObject, NamespaceAliasObject, TemplateAliasObject
from illuminate.code_models.directive_objects import UsingNamespaceObject, \
        UsingDeclarationObject
from illuminate.collections.unit_summary import UnitSummary

import illuminate.rules.code_model_map as cmm

cindex = ilcc.clang.cindex


@cmm.default_code_model("header")
class HeaderObject(object):

    
    def __init__(self, node: cindex.Cursor, header_file: str, parser: "illuminate.parsers.cpp_parse.ClangCppParse", \
            project_root,
            unit_name: str=""):
        
        self.unit_headers = None
        self.header_file = os.path.join(project_root, header_file)
        self.header_relpath = header_file
        self.unit_name = unit_name

        self.base_namespace = NamespaceObject(None)

        self.unit_includes = []
        self.extern_includes = []
        self.comments = []
        self.parser = parser
        self.n_objs = 0

        self.summary = UnitSummary()
        self.summary.ref = self.header_file

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
            }


        return

    @property
    def header_logger(self):
        return il_cfg.logger.bind(log_parsed=il_cfg.log_parsed,
                log_object_deps=il_cfg.log_object_deps,
                log_module_deps=il_cfg.log_module_deps,
                project=il_cfg.project,
                package=il_cfg.package,
                header=self.header_file)

    def in_registry(self, hash_in: int) -> bool:
        return hash_in in self.hash_registry

    def register_object(self, cpo: ParseObject) -> None:
        if not self.in_registry(cpo.hash):
            self.hash_registry.append(cpo.hash)
            cpo.parse_id = self.n_objs
            self.n_objs += 1
        return

    def add_usr(self, obj: ParseObject) -> None:
        self.summary.identifier_map[obj.qualified_id] = obj.usr
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
            ref_node = child.get_definition()
        else:
            ref_node = child
        dep_obj = self.get_usr(ref_node.get_usr())

        if dep_obj is not None:
            po.dep_objs.append(dep_obj)
        else:
            po.dep_objs.append(self.header_add_object(ref_node))
        return dep_obj

    def header_add_object(self, node: cindex.Cursor) -> ParseObject:
        model = cmm.default_code_models[node.kind]
        obj = model(node, True).set_header(self).handle(node)
        self.header_add_fns[node.kind](obj)
        self.summary.usr_map[obj.usr] = obj
        self.summary.identifier_map[obj.qualified_id] = obj.usr
        return obj

    def header_add_class(self, _class: ClassObject) -> None:
        self.summary.all_objects.append(_class)
        self.summary.classes.append(_class)
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
        if not func.qualified_id in self.summary.functions.keys():
            self.summary.functions[func.qualified_id] = []
        self.summary.all_objects.append(func)
        self.summary.functions[func.qualified_id].append(func)
        return

    def header_add_template_class(self, temp: TemplateObject) -> None:
        self.summary.all_objects.append(temp)
        self.summary.template_classes.append(temp)
        return

    def header_add_template_function(self, tfunc: TemplateObject) -> None:
        if not tfunc.get_name() in self.summary.template_functions.keys():
            self.summary.template_functions[tfunc.get_name()] = []
        self.summary.all_objects.append(tfunc)
        self.summary.template_functions[tfunc.get_name()].append(tfunc)
        return

    def get_namespace_by_qualified_id(self, ns_id: str) -> typing.Union['NamespaceObject', None]:
        for ns in self.summary.namespaces:
            if ns.qualified_id == ns_id:
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

    def get_header_file(self) -> str:
        return self.header_file

    def handle_includes(self, project_root: str, working_dir: str, parse: cindex.TranslationUnit) -> None:

        
        for file_include in parse.get_includes():
            if not file_include.include.name in os.listdir(working_dir) and \
                    file_include.include.name.startswith(project_root) and \
                    file_include.include.name not in self.summary.extern_headers:

                self.summary.extern_headers.append(str(file_include.include.name))

            elif file_include.include.name in os.listdir(working_dir) and \
                    file_include.include.name not in self.summary.unit_headers:

                
                self.summary.unit_headers.append(str(file_include.include.name))

        
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

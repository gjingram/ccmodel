from clang import cindex, enumerations
import typing
import os
import copy
import regex
import warnings
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
from .template import TemplateObject, PartialSpecializationObject
from .template_param import TemplateParamObject, re_param
from .enumeration import EnumObject, EnumConstDeclObject
from .comment_object import CommentObject
from .alias_objects import (
    TypeDefObject,
    TypeAliasObject,
    NamespaceAliasObject,
    TemplateAliasObject,
)
from .directive_objects import UsingNamespaceObject, UsingDeclarationObject
from ..utils import summary
from ..utils.code_utils import (
        re_targlist,
        split_bracketed_list,
        split_scope_list,
        replace_template_params_str,
)
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser

cindex = ccm_cc.clang.cindex
HeaderSummary = summary.HeaderSummary

@cmm.default_code_model("header")
class HeaderObject(object):
    def __init__(
        self,
        header_file: str,
    ):

        self.header_file = header_file
        self.directory = os.path.join(*header_file.split(os.sep)[:-1])
        self.base_namespace = parser.global_namespace()
        self.unit_includes = []
        self.extern_includes = []
        self.comments = []
        self.n_objs = 0
        self.summary = HeaderSummary(parser.summary)
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
            "CLASS_TEMPLATE_PARTIAL_SPECIALIZATION": self.header_add_partial_spec,
        }

        return

    @property
    def header_logger(self):
        return ccm_cfg.logger.bind(
            log_parsed=ccm_cfg.log_parsed,
            log_object_deps=ccm_cfg.log_object_deps,
            header=self.header_file,
        )

    def get_last_modified_time(self) -> None:
        try:
            self.summary.last_modified = os.path.getmtime(self.header_file)
        except:
            warnings.warn(
                f'Could not obtain last file modification time for "{self.header_file}".'
            )
            self.summary.last_modified = 0
        return

    def register_template(self, sid: str, key: typing.Tuple[str], obj: "TemplateObject") -> None:
        if not sid in self.summary.template_specializations:
            self.summary.template_specializations[sid] = {}
        if not key in self.summary.template_specializations[sid]:
            self.summary.template_specializations[sid][key] = obj
        if not sid in parser.summary.template_specializations:
            parser.summary.template_specializations[sid] = {}
        if not key in parser.summary.template_specializations[sid]:
            parser.summary.template_specializations[sid][key] = obj
        return

    def get_template_specialization(self, sid: str) -> typing.Optional[typing.Dict]:
        if not sid in parser.summary.template_specializations:
            return None
        return parser.summary.template_specializations[sid]

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
            return parser.summary.usr_map[usr]
        except KeyError:
            pass
        return None

    def header_extend_dep(self, dep_obj: "ParseObject", obj: "ParseObject") -> None:
        for dep in dep_obj.dependencies:
            obj.dependencies.append(dep.definition)
            self.header_extend_dep(dep, obj)
        return

    def header_get_dep(self, child: cindex.Cursor, po: ParseObject) -> "ParseObject":

        # First attempt at dependency resolution is just to try
        # to use clang to get a definition
        ref_node = None
        if not child.is_definition():
            test_node = child.get_definition()
            ref_node = child if test_node is None else test_node
        else:
            ref_node = child

        # If we have a CLASS_DECL, we need to check if the 
        # class is a template specialization, because if it 
        # is, clang will likely point toward the correct semantic
        # parent, but the parent will only have the primary
        # template or partial specialization associated with
        # the full specialization as a child, and the
        # parent-child relationship will be broken for the 
        # class.
        is_template_spec = False
        if (
            ref_node.kind == cindex.CursorKind.CLASS_DECL or
            ref_node.kind == cindex.CursorKind.STRUCT_DECL
        ):
            tmatch = re_targlist.match(child.displayname)
            is_template_spec = tmatch is not None


        # Clang dependency resolution fails if the "definition"
        # kind is NO_DECL_FOUND or if the definition of a 
        # CXX_BASE_SPECIFIER node is also a CXX_BASE_SPECIFIER
        clang_dep_resolved = True
        clang_dep_resolved &= (ref_node.kind != cindex.CursorKind.NO_DECL_FOUND)
        clang_dep_resolved &= (ref_node.kind != cindex.CursorKind.CXX_BASE_SPECIFIER)
        clang_dep_resolved &= not is_template_spec

        # If the node was found via clang, first see if the node's 
        # been parsed with a usr lookup. If not, force parse the
        # object if it makes sense.
        dep_obj = None
        if clang_dep_resolved:
            dep_obj = self.get_usr(ref_node.get_usr())
            if dep_obj:
                return dep_obj

            # Recurse up through the ref node parents
            # looking either for namespace/class/template
            # nodes or a usr that's already been parsed
            ref_node_parents = []
            nearest_parent_obj = None
            semantic_parent = ref_node.semantic_parent
            while semantic_parent and semantic_parent.kind != cindex.CursorKind.TRANSLATION_UNIT:
                nearest_parent_obj = self.get_usr(semantic_parent.get_usr())
                if nearest_parent_obj:
                    break
                ref_node_parents.append(semantic_parent)
                semantic_parent = semantic_parent.semantic_parent

            # If there are no parents and there's no nearest object, this
            # dependency node might be trouble. Check to see if it's a 
            # directive dependency, i.e., the child could be a first-level
            # namespace or a top-level object.
            proceed = (
                    len(ref_node_parents) or
                    nearest_parent_obj or
                    (
                        semantic_parent and
                        semantic_parent.kind == cindex.CursorKind.TRANSLATION_UNIT
                    )
            )

            # Define a function that gets nodes of concern for minimal parsing
            # of objects in the beeline to the dependency object
            def nodes_of_concern(node: cindex.Cursor, start_node: cindex.Cursor):
                active_namespaces = []
                active_using_decls = {}
                start_out = None
                for x in node.get_children():
                    if x.kind == cindex.CursorKind.USING_DIRECTIVE:
                        udir_temp = UsingNamespaceObject(x)
                        udir_temp.process_child(x, set_names=False)
                        active_namespaces.append(udir_temp["using_namespace"])
                    if x.kind == cindex.CursorKind.USING_DECLARATION:
                        udecl_temp = UsingDeclarationObject(x)
                        udecl_temp.process_child(x, set_names=False)
                        active_using_decls[udecl_temp["type_name"]] = \
                                udecl_temp["using_type"]
                    if x == start_node:
                        start_out = x
                        break
                return active_namespaces, active_using_decls, start_out

            # Define a function that either parses and object completely
            # or partially depending on whether the object is a namespace
            # object, some other kind of object, or associated with the ref
            # node
            def create_dep_object(node: cindex.Cursor, parent: "ParseObject") -> "ParseObject":
                active_namespaces = []
                active_using_decls = {}
                if node.semantic_parent is not None:
                    active_namespaces, active_using_decls, check_node = \
                            nodes_of_concern(node.semantic_parent, node)
                    if check_node != node:
                        return None
                header_use = parser.get_header(node.location.file.name)
                model_ctor = cmm.default_code_models[node.kind]
                template_parents = [*parent["template_parents"], parent] if isinstance(parent, TemplateObject) \
                        else parent["template_parents"]

                obj_out = None
                if isinstance(parent, NamespaceObject) and node is not ref_node:
                    obj_out = parent.process_child(node)
                    obj_out["force_parse"] = True
                    obj_out.set_header(header_use)
                    obj_out.set_scope(parent)
                    obj_out.add_active_namespaces(active_namespaces)
                    obj_out.add_active_directives(active_using_decls)
                    obj_out.set_parse_level(parent["parse_level"])
                    obj_out.do_handle(node)
                    ParseObject.handle(obj_out, node)
                else:
                    obj_out = model_ctor(node, True)\
                            .set_header(header_use)\
                            .add_template_parents(template_parents)\
                            .set_scope(parent)\
                            .add_active_namespaces(active_namespaces)\
                            .add_active_directives(active_using_decls)\
                            .set_parse_level(parent["parse_level"])\
                            .do_handle(node)\
                            .handle(node)
                return obj_out


            if proceed:

                # Create a chain of objects straight down to the dependency
                # object, startight either at the first ref node or at
                # the nearest parent object, if it exists
                start_node = ref_node if not len(ref_node_parents) else \
                        ref_node_parents[-1]
                if not nearest_parent_obj:

                    # Run along the semantic parent children collecting
                    # directives until the last ref node parent is encountered,
                    # and start the beeline back to the dependency
                    nearest_parent_obj = create_dep_object(start_node, self.base_namespace)
                    if len(ref_node_parents):
                        ref_node_parents.pop()
                    if start_node == ref_node:
                        return nearest_parent_obj

                while len(ref_node_parents):
                    node_use = ref_node_parents[-1]
                    nearest_parent_obj = create_dep_object(node_use, nearest_parent_obj)
                    ref_node_parents.pop()

                return create_dep_object(ref_node, nearest_parent_obj)

                
        # If we get here, it's because clang had a hard time with a dependency
        # node, e.g. a template class with a template base. In these cases,
        # there's no valid node that clang will point us to, and we'll either
        # find the node by name in the parser identifier map, by name in the
        # parser template specializations map, or it won't be found at all.
        # In the latter case, the best that can be done is to return a string
        # and warn that the dependency wasn't found.

        # Try to find the object by displayname taking into account active
        # namespace directives and declarations

        def vary_name_over_namespaces(name_use: str) -> typing.List[str]:
            names = [name_use]
            if child.semantic_parent and child.semantic_parent.spelling != "":
                names.append(child.semantic_parent.spelling + "::" + name_use)
            names.extend([ns + "::" + name_use for ns in po.active_namespaces])
            return names

        def vary_name_over_using_directives(name_use: str) -> typing.List[str]:
            over_ns = vary_name_over_namespaces(name_use)
            out = []
            for audkey, aud in po.active_using_directives.items():
                for name in over_ns:
                    out.append(name.replace(audkey, aud))
            out.extend(over_ns)
            out = list(set(out))
            return out

        if parser.summary.name_in_summary(child.displayname if not ref_node else ref_node.displayname):
            return summary.summary[child.displayname]

        for name in vary_name_over_using_directives(child.displayname if not ref_node else ref_node.displayname):
            if parser.summary.name_in_summary(name):
                return parser.summary[name]

        # Still haven't found anything, so try a template replacement and lookup
        template_name_use = replace_template_params_str(
                child.displayname if not ref_node else ref_node.displayname,
                po["template_parents"]
                )
        try_template = None
        template_inst = None
        for tname in vary_name_over_using_directives(template_name_use):

            # Split the tname into its scope sections
            name_parts = split_scope_list(tname)

            # Each of these name parts could be a template that needs
            # to be instantiated, so check for a template and 
            # instantiate one of necessary.
            test_name = ""
            for name in name_parts:
                match_template = re_targlist.match(name)
                if not match_template:
                    if test_name == "":
                        test_name = name
                    else:
                        test_name = test_name + "::" + name
                    continue
                if test_name == "":
                    test_name = match_template.group("t_name")
                else:
                    test_name = test_name + "::" + match_template.group("t_name")
                try_template = self.header_match_template_ref(
                        test_name,
                        split_bracketed_list(
                            match_template.group("t_arglist")
                            ),
                        child.get_usr())
                test_name = test_name + match_template.group("t_section")

                # This TemplateObject method will bounce back
                # None if it detects a template parameter that's
                # been replaced, otherwise it will instantiate
                # a class/function from the template because
                # otherwise one won't exist.
                if try_template:
                    tparents = [*po["template_parents"], po] if isinstance(po, TemplateObject) \
                            else po["template_parents"]
                    test_name = replace_template_params_str(
                            test_name,
                            tparents
                            )
                    template_inst = try_template.instantiate(
                            test_name,
                            split_bracketed_list(
                                match_template.group("t_arglist")
                                ),
                            )
            if template_inst:
                return template_inst
            if try_template:
                return try_template

        # If we're here, we're pretty much S.O.L. on this dependency,
        # so just return the child's displayname because the dependency
        # is totally incapable of being resolved. Warn.
        warnings.warn(f"Can't resolve the dependency {child.displayname} for {po['scoped_displayname']}.")
        return child.displayname

    def header_match_template_ref(
            self, qual: str, params: typing.Tuple[str], usr: typing.Optional[str] = None
    ) -> typing.Optional["TemplateObject"]:

        # In this method, the assumption is you're looking for a dependency.
        # If no template has been parsed as a primary template with qual
        # as its name, you won't find anything here.
        if not qual in parser.template_specializations:
            return None

        # The gist of this method is that, if a primary template with qual
        # as its name has been parsed, it will be stored in a dictionary
        # with a dictionary value whose keys are a tuple of replaced
        # template params (e.g., ('#', '#', 'int#', '[bool]', '[#...]'))
        # so that given a template name the most specific template object
        # can be returned for a dependency request.

        # First, look for all specializations that can be matched to
        # the input params tuple
        specializations = parser.template_specializations[qual]
        possible_match_keys = []
        for spec_key in [x for x in specializations.keys() if x != "primary"]:
            if len(spec_key) == len(params):
                possible_match_keys.append(list(spec_key))
            elif len(params) > len(spec_key) and spec_key[-1].endswith("..."):
                possible_match_keys.append(list(spec_key))
            elif len(params) < len(spec_key):
                start_list = copy.deepcopy(spec_key)
                default_or_variadic = True
                end_is_variadic = False
                for remain in spec_key[len(params) :]:
                    default_type = re_param.search(remain)
                    if default_type:
                        default_type = default_type.group("default")
                    default = (
                        default_type is not None
                        and default_type != "#"
                        and not default_type.endswith("...")
                    )
                    variadic = remain.endswith("...")
                    default_or_variadic &= default or variadic
                if default_or_variadic:
                    possible_match_keys.append(spec_key)

        # Begin weeding out keys that don't make sense given the params
        # tuple specifics
        match_copies = copy.deepcopy(possible_match_keys)
        param_copy = list(copy.deepcopy(params))
        for pspec_idx, pspec_key in enumerate(match_copies):
            for param_idx, param in enumerate(param_copy):
                if param_idx < len(pspec_key):
                    if pspec_key[param_idx].endswith("#"):
                        continue
                    elif pspec_key[param_idx] == param:
                        continue
                    elif (
                        re_param.search(pspec_key[param_idx]).groupdict()["default"]
                        is not None
                    ):
                        continue
                    elif param_idx == len(params) - 1:
                        for remain in pspec_key[param_idx:]:
                            default = re_param.search(remain).group("default")
                            if default is not None:
                                continue
                            elif remain.endswith("..."):
                                continue
                            else:
                                possible_match_keys.pop(pspec_idx)
                                break
                        continue
                    else:
                        possible_match_keys.pop(pspec_idx)
                        break
                elif param_idx >= len(pspec_key) - 1 and pspec_key[-1] == "...":
                    continue
                else:
                    possible_match_keys.pop(pspec_idx)
                    break

        # Find and return the specialization that's most
        # specific to the params tuple
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
                if pmatch[-1].endswith("...") and len(params) > len(pmatch):
                    min_pound += len(params) - len(pmatch) - 1
        return match

    def header_add_unknown(self, obj: "ParseObject") -> None:
        self.summary.all_objects.append(obj)
        return

    def header_add_object(
        self, scope: "ParseObject", node: cindex.Cursor
    ) -> ParseObject:
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
        scope_use = self.get_usr(node.semantic_parent.get_usr())
        if scope_use is None:
            scope_use = scope
        parent = node.semantic_parent
        tparents = []
        while parent is not None and parent.kind != cindex.CursorKind.TRANSLATION_UNIT:
            if (
                parent.kind == cindex.CursorKind.FUNCTION_TEMPLATE
                or parent.kind == cindex.CursorKind.CLASS_TEMPLATE
            ):
                try:
                    temp = self.get_usr(parent.get_usr())
                    tparents.append(temp)
                except KeyError:
                    pass
            parent = parent.semantic_parent
        obj = (
            model(node, force=True)
            .set_header(self)
            .set_scope(scope_use)
            .add_active_namespaces(scope_use.active_namespaces)
            .add_active_directives(scope_use.active_using_directives)
            .add_template_parents(tparents)
            .set_parse_level(scope_use["parse_level"])
            .do_handle(node)
            .handle(node)
        )
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

    def get_namespace_by_scoped_id(
        self, ns_id: str
    ) -> typing.Union["NamespaceObject", None]:
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
            if not include_name in parser.headers:
                self.unit_includes.append(include_name)
            else:
                self.extern_includes.append(include_name)
        return

    def handle(self, node: cindex.Cursor) -> "HeaderObject":

        self.summary.comments[self.header_file] = []

        # Get all comments in the file first
        for tok in node.get_tokens():
            if tok.kind == cindex.TokenKind.COMMENT:
                self.summary.comments[self.header_file].append(CommentObject(tok))
        pdb.set_trace()
        self.base_namespace.set_header(self)
        self.base_namespace.do_handle(node)
        self.base_namespace.handle(node)

        return self

    def _handleDiagnostic(self, diag) -> bool:

        diagMsg = "{}\nline {} column {}\n{}".format(
            str(diag.location.file),
            diag.location.line,
            diag.location.column,
            diag.spelling,
        )

        if diag.severity == cindex.Diagnostic.Warning:
            raise RuntimeWarning(diagMsg)

        if diag.severity >= cindex.Diagnostic.Error:
            raise RuntimeError(diagMsg)

        return

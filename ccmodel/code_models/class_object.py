from clang import cindex, enumerations
import typing
import pdb
import copy

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from .namespace import NamespaceObject
from .member import MemberObject
from .member_function import MemberFunctionObject
from .types import class_type
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser


@cmm.default_code_model(cindex.CursorKind.CLASS_DECL)
@cmm.default_code_model(cindex.CursorKind.STRUCT_DECL)
class ClassObject(NamespaceObject):
    def __init__(
        self,
        node: typing.Optional[cindex.Cursor] = None,
        force: bool = False,
        name: typing.Optional[str] = None,
    ):
        NamespaceObject.__init__(self, node, force)

        self.info["base_classes"] = {}
        self.info["distant_ancestors"] = []
        self.info["constructors"] = {}
        self.info["destructors"] = {}
        self.info["converting_constructors"] = {}
        self.info["conversion_functions"] = {}
        self.info["class_type"] = "CONCRETE"
        self.info["is_final"] = False
        self["export_to_scope"] = False
        self["is_class"] = True
        self["is_namespace"] = False

        if name is not None:
            self["id"] = name
            self["displayname"] = name
            self["is_anonymous"] = False
            if node is not None:
                self.determine_scope_name(node)

        self["is_union"] = False

        return

    def set_template_ref(self, templ: "TemplateObject") -> "ClassObject":
        self["is_template"] = True
        self["template_ref"] = templ
        return self

    def process_child(self, child: cindex.Cursor) -> typing.Optional["ParseObject"]:
        out = NamespaceObject.process_child(self, child)
        if out:
            return out

        tparents = self["template_parents"]
        scope_use = self["scope"] if self["export_to_scope"] else self

        # Resolve parent ClassObject when creating module links
        if child.kind == cindex.CursorKind.CXX_BASE_SPECIFIER:
            self.add_class_parent_type(child)
            return None

        if child.kind == cindex.CursorKind.CONSTRUCTOR:
            header_use = parser.get_header(child.location.file.name)
            cpo_class = self.get_child_type(child)
            ctor = cpo_class(child, self["force_parse"])
            ctor.add_template_parents(tparents).set_header(
                header_use
            ).set_scope(scope_use).add_active_namespaces(self.active_namespaces)\
                    .add_active_directives(self.active_using_directives)\
                    .set_parse_level(self["parse_level"])\
                    .mark_ctor(True).do_handle(child)
            if ctor.no_decl:
                return None
            self.add_class_constructor(ctor)
            if ctor["is_converting_ctor"]:
                self.add_class_conversion_function(ctor)
            return ctor

        if child.kind == cindex.CursorKind.DESTRUCTOR:
            header_use = parser.get_header(child.location.file.name)
            cpo_class = self.get_child_type(child)
            dtor = cpo_class(child, self["force_parse"])
            dtor.add_template_parents(tparents).set_header(
                header_use
            ).set_scope(scope_use).add_active_namespaces(self.active_namespaces)\
                    .add_active_directives(self.active_using_directives)\
                    .set_parse_level(self["parse_level"])\
                    .mark_dtor(True).do_handle(child)
            if dtor.no_decl:
                return None
            self.add_class_destructor(dtor)
            return dtor

        if child.kind == cindex.CursorKind.CXX_METHOD:
            meth = self.create_clang_child_object(child)
            if not meth.do_handle(child):
                return None
            self.add_function(meth)
            return meth

        if child.kind == cindex.CursorKind.CONVERSION_FUNCTION:
            conv = self.create_clang_child_object(child)
            conv.mark_conversion(True)
            if conv.no_decl:
                return None
            self.add_class_conversion_function(conv)
            return conv

        if child.kind == cindex.CursorKind.CXX_FINAL_ATTR and not self["is_final"]:
            self["is_final"] = True

        return None

    @if_handle
    def handle(self, node: cindex.Cursor) -> "ClassObject":
        NamespaceObject.handle(self, node)

        children = []
        self.extend_children(node, children)
        for child in children:
            child_obj = self.process_child(child)
            if child_obj is not None:
                child_obj.handle(child)

        self.extend_with_inheritance()
        return self

    def add_class_parent_type(self, class_in: cindex.CursorKind) -> None:
        base = self["header"].header_get_dep(class_in, self)

        if base and type(base) is not str:
            while (
                    "aliased_object" in base.info or
                    "object" in base.info
            ):
                if "aliased_object" in base.info:
                    base = base["aliased_object"]
                    if type(base) is str:
                        break
                if "object" in base.info:
                    base = base["object"]
                    if type(base) is str:
                        break

        if type(base) is str:
            base = (
                    ClassObject(class_in, False)
                    .add_template_parents(self["template_parents"])
                    .set_header(self["header"])
                    .set_scope(self)
                    .add_active_namespaces(self.active_namespaces)
                    .add_active_directives(self.active_using_directives)
                    .set_parse_level(self["parse_level"])
                    .do_handle(class_in)
            )
        base_append = {
            "access_specifier": class_in.access_specifier.name,
            "base_class": base,
        }


        if type(base) is str:
            self["base_classes"][class_in.displayname] = base_append
        else:
            self["base_classes"][base["displayname"]] = base_append
        return

    def extend_with_inheritance(self) -> None:
        for the_base in self["base_classes"].values():
            base = the_base["base_class"]
            spec = the_base["access_specifier"]
            got_object = False
            if type(base) is str:
                return
            for func in base["functions"].values():
                if (
                    func["id"] == "operator="
                    or func["is_ctor"]
                    or func["is_dtor"]
                    or func["access_specifier"] == "PRIVATE"
                ):
                    continue
                if func["displayname"] in self["functions"]:
                    continue
                func_use = copy.copy(func)
                func_use["inherited"] = True
                self._route_inheritance_by_access_spec(spec, func_use)
                func_use.update_class_type(self)
                self["functions"][func_use["displayname"]] = func_use
            for cfunc in base["conversion_functions"].values():
                if cfunc["id"] == "operator=":
                    continue
                if cfunc["displayname"] in self["conversion_functions"]:
                    continue
                if cfunc["access_specifier"] == "PRIVATE":
                    continue
                cfunc_use = copy.copy(cfunc)
                cfunc_use["inherited"] = True
                self._route_inheritance_by_access_spec(spec, cfunc_use)
                cfunc_use.update_class_type(self)
                self["conversion_functions"][cfunc_use["displayname"]] = cfunc_use
            self._route_inheritance_by_kw("class_templates", base, spec)
            self._route_inheritance_by_kw("partial_specializations", base, spec)
            self._route_inheritance_by_kw("function_templates", base, spec)
            self._route_inheritance_by_kw("typedefs", base, spec)
            self._route_inheritance_by_kw("classes", base, spec)
            self._route_inheritance_by_kw("structs", base, spec)
            self._route_inheritance_by_kw("unions", base, spec)
            self._route_inheritance_by_kw("enumerations", base, spec)
            self._route_inheritance_by_kw("namespace_aliases", base, spec)
            self._route_inheritance_by_kw("type_aliases", base, spec)
            self._route_inheritance_by_kw("template_aliases", base, spec)
            self._route_inheritance_by_kw("using_declarations", base, spec)
            self._route_inheritance_by_kw("variables", base, spec)
            self._distant_ancestor_recurse(base, self["distant_ancestors"])
        return

    def _distant_ancestor_recurse(
        self, base: "ClassObject", da_array: typing.List[str]
    ) -> None:

        if len(base["base_classes"]) > 0:
            for base_distant in base["base_classes"].values():
                base._distant_ancestor_recurse(base_distant["base_class"], da_array)
                da_array.append(base_distant["base_class"]["scoped_displayname"])
        return

    def _route_inheritance_by_kw(
        self,
        kw: str,
        base: typing.Union["ClassObject", "TemplateObject", "AliasObject"],
        spec: str,
    ) -> None:
        for obj in base[kw].values():
            if obj["displayname"] in self[kw]:
                continue
            if obj["access_specifier"] == "PRIVATE":
                continue
            obj_use = copy.copy(obj)
            obj_use["inherited"] = True
            self._route_inheritance_by_access_spec(spec, obj_use)
            self[kw][obj_use["displayname"]] = obj_use
        return

    def _route_inheritance_by_access_spec(self, spec: str, obj: "ParseObject") -> None:
        if spec == "PROTECTED" and obj["access_specifier"] == "PUBLIC":
            obj["access_specifier"] = "PROTECTED"
        elif spec == "PRIVATE":
            obj["access_specifier"] = "PRIVATE"
        return

    def add_class_constructor(self, ctor: "MemberFunctionObject") -> None:
        self["all_objects"].append(ctor)
        self["constructors"][ctor["displayname"]] = ctor
        if ctor["is_converting_ctor"]:
            self["converting_constructors"][ctor["displayname"]] = ctor
        return

    def add_class_destructor(self, dtor: "MemberFunctionObject") -> None:
        self["all_objects"].append(dtor)
        self["destructors"][dtor["displayname"]] = dtor
        return

    def add_class_conversion_function(self, conv: "MemberFunctionObject") -> None:
        if not conv in self["all_objects"]:
            self["all_objects"].append(conv)
        self["conversion_functions"][conv["displayname"]] = conv
        return

    def set_class_type(self, type_in: int) -> None:
        ctype_int = class_type[self["class_type"]]
        type_str = ""
        for key, item in class_type.items():
            if type_in == item:
                type_str = key
                break
        self["class_type"] = type_str if type_in > ctype_int else self["class_type"]
        return

    def get_parents(self) -> typing.Tuple[str]:
        return self["base_classes"]

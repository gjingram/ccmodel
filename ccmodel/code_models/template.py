from clang import cindex, enumerations
import typing
import pdb
import copy
import regex

from .decorators import if_handle, append_cpo, add_obj_to_header_summary
from .parse_object import ParseObject
from ..utils.code_utils import (
    replace_template_params,
    replace_template_params_str,
    re_targlist,
    split_bracketed_list,
    split_scope_list,
    find_template_defs,
)
from ..utils import summary
from .template_param import TemplateParamObject, re_type_param, re_nontype_param
from ..rules import code_model_map as cmm
from ..parsers import cpp_parse as parser


@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE)
@cmm.default_code_model(cindex.CursorKind.FUNCTION_TEMPLATE)
class TemplateObject(ParseObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)

        self.info["object"] = None
        self.info["object_class"] = None
        self.info["is_alias"] = False
        self.info["template_parameters"] = {}
        self.info["is_primary"] = True
        self.info["is_partial"] = False
        self.info["template_ref"] = None
        self.info["n_template_parameters"] = -1
        self.info["is_method_template"] = False
        self.info["is_function_template"] = False

        if node is not None:
            self.determine_scope_name(node)

        return

    def is_function_template(self, is_it: bool) -> "TemplateObject":
        self["is_function_template"] = is_it
        return self

    def is_method_template(self, is_it: bool) -> "TemplateObject":
        self["is_method_template"] = is_it
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> "TemplateObject":

        children = []
        self.extend_children(node, children)

        node_children = []
        self["n_template_parameters"] = 0
        for child in children:
            if child.kind == cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            elif child.kind == cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
                self.handle_template_parameter(child)
                node_children.append(child)

            else:
                continue
            self["n_template_parameters"] += 1

        tparams = []
        tnames = []
        for x in self["template_parameters"].values():
            if x["is_variadic"]:
                tparams.append(x.param + "...")
                tnames.append(x["id"] + "...")
                continue
            tparams.append(x.param)
            tnames.append(x["id"])

        self["displayname"] = self["id"] + \
                    f"<{', '.join(tnames)}>"

        tparents = [*self["template_parents"], self]
        if self["is_alias"]:
            self[
                "scoped_displayname"
            ] += f"<{', '.join(tparams)}>"
            self["scoped_displayname"] = replace_template_params_str(
                    self["scoped_displayname"],
                    tparents)
        else:
            self["scoped_displayname"] = self["scope"]["scoped_displayname"] + \
                    "::" + self["id"] + f"<{', '.join(tparams)}>" if \
                    self["scope"]["id"] != "GlobalNamespace" else \
                    self["id"] + f"<{', '.join(tparams)}>"
            self["scoped_displayname"] = replace_template_params_str(
                self["scoped_displayname"], tparents
            )
            self.template_params_replaced = True
        for child_node, param in zip(
            node_children, self["template_parameters"].values()
        ):
            param.handle(child_node)


        header_use = parser.get_header(node.location.file.name)
        if node.kind == cindex.CursorKind.CLASS_TEMPLATE:
            self["object_class"] = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self["object"] = (
                self["object_class"](node, True)
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self["scope"])
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_template_ref(self)
                .set_parse_level(self["parse_level"])
                .do_handle(node)
            )
            if not self["object"]:
                return None
            self["object"].handle(node)
            self["object"]["kind"] = "CLASS_DECL"
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
            self["is_primary"] = False
            self["is_partial"] = True
            self["object_class"] = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self["object"] = (
                self["object_class"](node, True)
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self["scope"])
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_template_ref(self)
                .set_parse_level(self["parse_level"])
                .do_handle(node)
            )
            if not self["object"]:
                return None
            self["object"].handle(node)
            self["object"]["kind"] = "CLASS_DECL"
        elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            if self["is_function_template"]:
                self["object_class"] = cmm.default_code_models[
                    cindex.CursorKind.FUNCTION_DECL
                ]
            elif self["is_method_template"]:
                self["object_class"] = cmm.default_code_models[
                    cindex.CursorKind.CXX_METHOD
                ]
            self["object"] = (
                self["object_class"](node, True)
                .add_template_parents(tparents)
                .set_header(header_use)
                .set_scope(self["scope"])
                .add_active_namespaces(self.active_namespaces)
                .add_active_directives(self.active_using_directives)
                .set_template_ref(self)
                .set_parse_level(self["parse_level"])
                .do_handle(node)
            )
            if not self["object"]:
                return None
            self["object"].handle(node)
            signature = "(" + ", ".join([x["type"] for x in self["object"]["params"].values()]) + \
                    ")"

            self["displayname"] += signature
            self["scoped_displayname"] += signature

            self["scoped_displayname"] = replace_template_params_str(
                    self["scoped_displayname"],
                    tparents)

            self["object"]["displayname"] = self["displayname"]
            self["object"]["scoped_displayname"] = self["scoped_displayname"]

            self["object"]["scoped_displayname"] = replace_template_params_str(
                    self["object"]["scoped_displayname"],
                    tparents)

            if self["is_function_template"]:
                self["object"]["kind"] = "FUNCTION_DECL"
            elif self["is_method_template"]:
                self["object"]["kind"] = "CXX_METHOD"
        else:
            if self["is_partial"]:
                return None

        self["header"].register_object(self)
        if not self["is_definition"]:
            self["definition"] = self["header"].get_usr(node.referenced.get_usr())

        if not self["is_partial"]:
            ParseObject.handle(self, node)

        self["n_template_parameters"] = len(self["template_parameters"])
        self.resolve_primary_ref()

        return self

    def handle_template_parameter(self, node: cindex.Cursor) -> None:

        using_cls = self.get_child_type(node)

        header_use = parser.get_header(node.location.file.name)
        template_param = using_cls(self, node)
        template_param.set_header(header_use)
        template_param.add_active_namespaces(self.active_namespaces)
        template_param.add_active_directives(self.active_using_directives)
        template_param.set_scope(self)
        template_param.add_template_parents([*self["template_parents"], self])
        template_param.set_parse_level(self["parse_level"])
        template_param["force_parse"] = True
        template_param["object"] = self["object"]
        template_param.do_handle(node)
        self.add_template_param(template_param)

        return

    def add_template_param(
        self, param: typing.Union["TemplateObject", "TemplateParamObject"]
    ) -> None:
        self["template_parameters"][param["id"]] = param
        return

    def resolve_primary_ref(self) -> None:
       
        # The template specialization lookup dictionary is keyed by
        # a scoped displayname down to the id level, where the 
        # displayname is replaced with id. A nested dictionary
        # with the generic template signature is then used to
        # refine a lookup
        using_sid = self["scope"]["scoped_displayname"] + "::" + self["id"] if \
                self["scope"]["id"] != "GlobalNamespace" else \
                self["id"]
        using_sid = replace_template_params_str(
                using_sid,
                [*self["template_parents"], self]
                )

        # If this template is a primary template, shove it onto the lookup
        # dictionary. If it isn't, grab the primary template in the lookup
        # dictionary. If it's an alias, this will be handled elsewhere.
        if self["is_primary"]:
            self["primary_ref"] = self
            param_key = []
            for param in self["template_parameters"].values():
                if param["is_variadic"]:
                    param_key.append(param.param.replace("#", "#..."))
                    continue
                param_key.append(param.param)
            self["header"].register_template(using_sid, tuple(param_key), self)
            return
        elif not self["is_alias"]:
            specializations = self["header"].get_template_specialization(using_sid)
            for spec in specializations.values():
                if spec["is_primary"]:
                    self["primary_ref"] = spec
        else:
            self["primary_ref"] = None

        return

    def instantiate(self, usr: str, t_args: typing.Tuple[str]) -> typing.Optional["ParseObject"]:

        # Copy the template, because I want to reuse the parameter
        # machinery during instantiation, which means modification
        t_copy = copy.deepcopy(self)
        t_copy_params = list(t_copy["template_parameters"].values())

        # If there's a replacement left, this request is to
        # instantiate a template rather than a full specialization
        for arg in t_args:
            arg_rep = replace_template_params_str(
                    arg,
                    [t_copy])
            if "#" in arg_rep:
                return None

        # Set template params with associated input arguments
        for t_arg_idx, t_arg in enumerate(t_args):
            t_copy_params[t_arg_idx]["parameter"] = t_arg
            t_copy_params[t_arg_idx].parameter_set = True
        for param_remain in t_copy_params[len(t_args) :]:
            if param_remain["default"] is not None:
                param_remain["parameter"] = param_remain["default"]
                param_remain.parameter_set = True
            if param_remain["is_variadic"]:
                param_remain["parameter"] = ""
                param_remain.parameter_set = True
        if len(t_args) > len(t_copy_params):
            if t_copy_params[-1]["is_variadic"]:
                for t_arg in t_args[len(t_copy_params) :]:
                    t_copy_params[-1]["parameter"] = ", ".join(
                        [t_copy_params[-1]["parameter"], t_arg]
                    )
            else:
                raise RuntimeError(
                    f"Too many template args: {t_args}, {t_copy['displayname']}"
                )

        # Copy the object and start replacing template params
        out = copy.deepcopy(self["object"])
        out["scope"] = self["scope"]
        out["id"] = self["id"]
        out["scoped_id"] = self["scope"]["scoped_id"] + "::" + self["id"] if \
                self["scope"]["id"] != "GlobalNamespace" else \
                self["id"]
        out["displayname"] = self["id"] + f"<{', '.join([x['parameter'] for x in t_copy['template_parameters'].values()])}>"
        out["scoped_displayname"] = self["scope"]["scoped_displayname"] + "::" + out["displayname"] if \
                self["scope"]["id"] != "GlobalNamespace" else \
                out["displayname"]

        # Create a function that will recurse over all child objects
        # replacing template parameters with arguments. Add the 
        # concrete objects to the summary as we go along.
        def all_objects_param_recurse(obj_in: typing.Union['ParseObject', typing.List[str]]) -> None:

            tparents = [t_copy, *obj_in["template_parents"]] if not isinstance(obj_in, TemplateObject) else \
                    [t_copy, *obj_in["template_parents"], obj_in]

            # Prepare the object to be instantiated
            obj_in["scoped_id"] = replace_template_params_str(
                    obj_in["scoped_id"], tparents)
            obj_in["scoped_displayname"] = replace_template_params_str(
                    obj_in["scoped_displayname"], tparents)
            obj_in["type"] = replace_template_params_str(
                    obj_in["type"], tparents)
            obj_in["usr"] = obj_in["scoped_displayname"]
            new_info = obj_in.info.copy()
            for key, val in obj_in.info.items():
                if type(val) is dict:
                    new_val = val.copy()
                    for valkey, valval in val.items():
                        valkey_new = replace_template_params_str(
                                valkey,
                                tparents)
                        del new_val[valkey]
                        new_val[valkey_new] = valval
                    new_info[key] = new_val
                if type(val) is str:
                    val_new = replace_template_params_str(
                            val,
                            tparents)
                    new_info[key] = val_new
            obj_in.info = new_info
            obj_in.template_params_replaced = True

            # Using the prepared usr, return if this object has already
            # been instantiated
            if obj_in["header"].summary.usr_in_parser_summary(obj_in["usr"]):
                return None

            # If a template object is encountered, resolve its primary ref
            if isinstance(obj_in, TemplateObject):
                obj_in.resolve_primary_ref()

            # If a template specialization is encountered, also resolve
            # its partial ref
            if isinstance(obj_in, PartialSpecializationObject):
                obj_in["partial_ref"] = obj_in["header"].header_match_template_ref(
                obj_in["primary_name"], obj_in.extract_params()
                )
                obj_in["dependencies"].append(obj_in["partial_ref"])

            # Add the object to the summary
            add_obj_to_header_summary(obj_in)

            def vary_name_over_namespaces(name_use: str) -> typing.List[str]:
                names = [name_use]
                names.extend([ns + "::" + name_use for ns in obj_in.active_namespaces])
                return names

            def vary_name_over_using_directives(name_use: str) -> typing.List[str]:
                over_ns = vary_name_over_namespaces(name_use)
                out = []
                for audkey, aud in self.active_using_directives.items():
                    for name in over_ns:
                        out.append(name.replace(audkey, aud))
                out.extend(over_ns)
                out = list(set(out))
                return out

            # Handle any inheritance associated with the template,
            # recursively instantiating any template objects that
            # can be.
            try:
                new_base_classes = obj_in["base_classes"].copy()
                for base_name, base in obj_in["base_classes"].items():

                    base_name_rep = replace_template_params_str(
                            base_name,
                            tparents)
                    match = re_targlist.match(base_name_rep)

                    base_rep = None
                    if match and "t_arglist" in match.groupdict() and \
                            match.group("t_arglist") is not None:

                        template_name_use = ""
                        if type(base["base_class"]) is str:
                            template_name_use = base["base_class"]
                        else:
                            template_name_use = base["base_class"]["scoped_displayname"]
                        template_name_use = replace_template_params_str(
                                template_name_use,
                                tparents
                                )

                        try_template = None
                        for tname in vary_name_over_using_directives(template_name_use):

                            name_parts = split_scope_list(tname)

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

                                try_template = self["header"].header_match_template_ref(
                                        test_name,
                                        split_bracketed_list(
                                            match.group("t_arglist")
                                            ),
                                        test_name + match.group("t_section")
                                        )
                                test_name = test_name + match_template.group("t_section")

                                if try_template is not None:
                                    test_name = replace_template_params_str(
                                            test_name,
                                            tparents
                                            )
                                    base_rep = try_template.instantiate(
                                            test_name,
                                            split_bracketed_list(
                                                match_template.group("t_arglist")
                                                ),
                                            )

                        if base_rep is None:
                            if try_template:
                                base_rep = try_template
                                break

                    acc_spec = base["access_specifier"]
                    del new_base_classes["base_classes"][base_name]
                    new_base_classes["base_classes"][base_name_rep] = {}
                    if type(base_rep) is not str:
                        new_base_classes["base_classes"][base_name_rep]["base_class"] = base_rep
                    else:
                        new_base_classes["base_classes"][base_name_rep]["base_class"] = base_name_rep
                    new_base_classes["base_classes"][base_name_rep]["access_specifier"] = acc_spec
                obj_in["base_classes"] = new_base_classes
            except KeyError:
                pass


            # Prepare contained objects to be added to the summary,
            # and recurse into them
            for obj in obj_in["all_objects"]:
                obj["scope"] = obj_in
                obj["scoped_id"] = obj["scope"]["scoped_id"] + "::" + obj["id"] if \
                    obj["scope"]["id"] != "GlobalNamespace" else \
                    obj["id"]
                obj["scoped_displayname"] = obj["scope"]["scoped_displayname"] + "::" + obj["displayname"] if \
                    obj["scope"]["id"] != "GlobalNamespace" else \
                    obj["displayname"]

                all_objects_param_recurse(obj)

                tparents = [t_copy, *obj["template_parents"], *obj_in["template_parents"]] if \
                        not isinstance(obj, TemplateObject) else \
                        [t_copy, *obj["template_parents"], *obj_in["template_parents"], obj]
                new_info = obj.info.copy()
                for key, val in obj.info.items():
                    if type(val) is dict:
                        new_val = val.copy()
                        for valkey, valval in val.items():
                            valkey_new = replace_template_params_str(
                                    valkey,
                                    tparents)
                            del new_val[valkey]
                            new_val[valkey_new] = valval
                        new_info[key] = new_val
                    if type(val) is str:
                        val = replace_template_params_str(
                                val,
                                tparents)
                        obj.info[key] = val
                obj.info = new_info
                obj.template_params_replaced = True
            return

        all_objects_param_recurse(out)
        return out


template_decl = r"\btemplate\s*<(?P<t_arglist>.*)>(?=\s*(:{2})?\w)?"
template_class = r"(?:class|struct)\s*(?P<cls_name>\w*)\s*<(?P<t_arglist>.*)>\s*"
template_class += r"(?::\s*(?:\s*(?:public|protected|private)\s*\w*,?\s*)*)?\s*{"
template_alias = (
    r"using\s*(?P<alias>\w*)\s*=\s*(?P<cls_name>\w*)\s*(?:<(?P<t_arglist>.*)>)?"
)

re_template_decl = regex.compile(template_decl)
re_template_class = regex.compile(template_class)
re_template_alias = regex.compile(template_alias)


@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION)
class PartialSpecializationObject(TemplateObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        TemplateObject.__init__(self, node, force)
        self["is_primary"] = False
        self["is_partial"] = True
        self["partial_ref"] = None
        self["is_alias"] = False
        self.info["primary_name"] = ""
        self.info["template_decl_params"] = []
        self.info["class_arglist"] = []
        self.partial_text = " ".join([x.spelling for x in node.get_tokens()]) if \
                node else ""
        return

    def add_template_decl_param(self, kind: int, ptype: str, name: str) -> None:
        ptype_use = ptype.replace(" ", "")
        name_use = name.replace(" ", "")
        self["template_decl_params"].append((kind, ptype_use, name_use))
        return

    def process_template_paramlist(self, paramlist) -> None:
        pmatches = split_bracketed_list(paramlist)
        for pmatch in pmatches:
            tmatch = re_type_param.match(pmatch)
            ntmatch = re_nontype_param.match(pmatch)
            if tmatch is not None:
                tmatch_groupdict = tmatch.groupdict()
                if (
                    "template_def" in tmatch_groupdict
                    and tmatch_groupdict["template_def"] is not None
                ):
                    self.add_template_decl_param("TEMPLATE", "#", tmatch.group("name"))
                elif (
                    "name" in tmatch_groupdict and tmatch_groupdict["name"] is not None
                ):
                    self.add_template_decl_param("TYPE", "#", tmatch.group("name"))
            elif ntmatch is not None:
                self.add_template_decl_param(
                    "NONTYPE", ntmatch.group("type"), ntmatch.group("name")
                )
        return

    def process_class_template_arglist(self, carglist) -> None:
        amatches = split_bracketed_list(carglist)
        for amatch in amatches:
            self["class_arglist"].append(amatch.replace(" ", ""))
        return

    def parse_template_decl(self) -> None:
        if "vector" in self["displayname"] and "double" in self["displayname"]:
            pdb.set_trace()
        template_defs = find_template_defs(self.partial_text)
        tdef_use = split_bracketed_list(template_defs[0])
        tmatch = re_template_decl.search(template_defs[0])
        self.process_template_paramlist(tmatch.group("t_arglist"))
        cmatch = None
        if not self["is_alias"]:
            cmatch = re_template_class.search(self.partial_text)
        else:
            cmatch = re_template_alias.search(self.partial_text)
        if cmatch is not None:
            self["primary_name"] = cmatch.group("cls_name")
            if (
                "t_arglist" in cmatch.groupdict()
                and cmatch.groupdict()["t_arglist"] is not None
            ):
                self.process_class_template_arglist(cmatch.group("t_arglist"))

        for pidx, param in enumerate(self["class_arglist"]):
            for tparam in self["template_decl_params"]:
                if param == tparam[2]:
                    self["class_arglist"][pidx] = "#"
        return

    def extract_params(self) -> typing.Tuple[str]:
        return tuple((arg for arg in self["class_arglist"]))

    @if_handle
    def handle(self, node: cindex.Cursor) -> "PartialSpecializationObject":
        TemplateObject.handle(self, node)
        if not self["is_alias"]:
            ParseObject.handle(self, node)
        self.parse_template_decl()
        self.resolve_partial_ref()
        if not self["is_alias"]:
            self["partial_ref"] = self
        return self

    def resolve_partial_ref(self) -> None:

        using_sid = self["scope"]["scoped_displayname"] + "::" + self["id"] if \
                self["scope"]["id"] != "GlobalNamespace" else \
                self["id"]
        using_sid = replace_template_params_str(
                using_sid,
                [*self["template_parents"], self]
                )

        self["header"].register_template(using_sid, tuple(self["class_arglist"]), self)
        return

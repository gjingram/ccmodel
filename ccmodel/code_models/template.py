from clang import cindex, enumerations
import typing
import pdb
import copy
import regex

from .decorators import (if_handle, 
        append_cpo, add_obj_to_header_summary)
from .parse_object import ParseObject
from ..utils.code_utils import (replace_template_params,
        replace_template_params_str, split_bracketed_list)
from .template_param import (TemplateParamObject,
        re_type_param, re_nontype_param)
from ..rules import code_model_map as cmm


@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE)
@cmm.default_code_model(cindex.CursorKind.FUNCTION_TEMPLATE)
class TemplateObject(ParseObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
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

    def is_function_template(self, is_it: bool) -> 'TemplateObject':
        self["is_function_template"] = is_it
        return self

    def is_method_template(self, is_it: bool) -> 'TemplateObject':
        self["is_method_template"] = is_it
        return self

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'TemplateObject':

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

        tparents = [*self["template_parents"], self]
        if self["is_alias"]:
            self["scoped_displayname"] += \
                    f"<{', '.join([x.param for x in self['template_parameters'].values()])}>"
        else:
            self["scoped_displayname"] = replace_template_params_str(
                    self["scoped_displayname"],
                    tparents
                    )
            self.template_params_replaced = True
        if not self["is_alias"] and not self["is_partial"]:
            ParseObject.handle(self, node)
        for child_node, param in zip(node_children, self["template_parameters"].values()):
            param.handle(child_node)

        if self["scoped_displayname"] in cmm.object_code_models:
            self["object_class"] = cmm.object_code_models[self["scoped_displayname"]]
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE:
            self["object_class"] = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self["object"] = self["object_class"](node, True).add_template_parents(tparents)\
                    .set_header(self["header"]).set_scope(self["scope"])\
                    .set_template_ref(self).handle(node)
        elif node.kind == cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
            self["is_primary"] = False
            self["is_partial"] = True
            self["object_class"] = cmm.default_code_models[cindex.CursorKind.CLASS_DECL]
            self["object"] = self["object_class"](node, True).add_template_parents(tparents)\
                    .set_header(self["header"]).set_scope(self["scope"])\
                    .set_template_ref(self).handle(node)
        elif node.kind == cindex.CursorKind.FUNCTION_TEMPLATE:
            if self["is_function_template"]:
                self["object_class"] = cmm.default_code_models[cindex.CursorKind.FUNCTION_DECL]
            elif self["is_method_template"]:
                self["object_class"] = cmm.default_code_models[cindex.CursorKind.CXX_METHOD]
            self["object"] = self["object_class"](node, True).add_template_parents(tparents)\
                    .set_header(self["header"]).set_scope(self["scope"])\
                    .set_template_ref(self).handle(node)
        else:
            if self["is_partial"]:
                return None

        self["header"].register_object(self)
        if not self["is_definition"]:
            self["definition"] = self["header"].get_usr(node.referenced.get_usr())
        
        self["n_template_parameters"] = len(self["template_parameters"])
        self.resolve_primary_ref()

        return self

    def handle_template_parameter(self, node: cindex.Cursor) -> None:

        using_cls = self.get_child_type(node)

        template_param = using_cls(node)
        template_param.set_header(self["header"])
        template_param.set_scope(self["scope"])
        template_param.add_template_parents([*self["template_parents"], self])
        template_param["force_parse"] = True
        template_param["object"] = self["object"]
        template_param["template"] = self
        self.add_template_param(template_param)

        return

    def add_template_param(self, param: typing.Union['TemplateObject',
        'TemplateParamObject']) -> None:
        self["template_parameters"][param["id"]] = param
        return

    def resolve_primary_ref(self) -> None:
        if self["is_primary"]:
            self["primary_ref"] = self
            self["header"].template_specializations[self["scoped_id"]] = {}
            self["header"].template_specializations[self["scoped_id"]][tuple(
                [x.param for x in self["template_parameters"].values()])] = \
                    self
            return
        elif not self["is_alias"]:
            specializations = self["header"].template_specializations[self["scoped_id"]]
            for spec in specializations.values():
                if spec["is_primary"]:
                    self["primary_ref"] = spec
        else:
            self["primary_ref"] = None

        return

    @append_cpo
    def instantiate(self, usr: str, t_args: typing.Tuple[str]) -> "ParseObject":
        t_copy = copy.deepcopy(self)
        t_copy_params = list(t_copy["template_parameters"].values())
        for t_arg_idx, t_arg in enumerate(t_args):
            t_copy_params[t_arg_idx]["parameter"] = t_arg
            t_copy_params[t_arg_idx].parameter_set = True
        for param_remain in t_copy_params[len(t_args):]:
            if param_remain["default"] is not None:
                param_remain["parameter"] = param_remain["default"]
                param_remain.parameter_set = True
            if param_remain["is_variadic"]:
                param_remain["parameter"] = ""
                param_remain.parameter_set = True
        if len(t_args) > len(t_copy_params):
            if t_copy_params[-1]["is_variadic"]:
                for t_arg in t_args[len(t_copy_params):]:
                    t_copy_params[-1]["parameter"] = \
                            ", ".join([t_copy_params[-1]["parameter"],
                                t_arg])
            else:
                raise RuntimeError(f"Too many template args: {t_args}, {t_copy['displayname']}")
        out = copy.deepcopy(self["object"])
        out["id"] = self["id"]
        out["displayname"] = out["id"] + \
                "<" + \
                ", ".join(t_args) + \
                ">"
        out["scoped_id"] = out["scope"]["scoped_id"] + "::" + out["id"]
        out["scoped_displayname"] = out["scope"]["scoped_displayname"] + \
                "::" + out["displayname"]
        out["usr"] = usr
        add_obj_to_header_summary(out["scoped_displayname"], out) 
        for obj in out["all_objects"]:
            obj["scoped_id"] = obj["scope"]["scoped_id"] + "::" + obj["id"]
            obj["scoped_displayname"] = obj["scope"]["scoped_displayname"] + \
                    "::" + obj["displayname"]
            replace_template_params_str(obj["scoped_displayname"],
                    [t_copy])
            obj.template_params_replaced = True
            obj["usr"] = obj["scoped_displayname"]
            add_obj_to_header_summary(obj["scoped_displayname"], obj)
        return

template_decl = r"\btemplate\s*<(?P<t_arglist>.*)>(?=\s*(:{2})?\w)"
template_class = r"(?:class|struct)\s*(?P<cls_name>\w*)\s*<(?P<t_arglist>.*)>"
template_alias = r"using\s*(?P<alias>\w*)\s*=\s*(?P<cls_name>\w*)\s*(?:<(?P<t_arglist>.*)>)?"

re_template_decl = regex.compile(template_decl)
re_template_class = regex.compile(template_class)
re_template_alias = regex.compile(template_alias)

@cmm.default_code_model(cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION)
class PartialSpecializationObject(TemplateObject):
    
    def __init__(self, node: cindex.CursorKind, force: bool = False):
        TemplateObject.__init__(self, node, force)
        self["is_primary"] = False
        self["is_partial"] = True
        self["partial_ref"] = None
        self["is_alias"] = False
        self.info["primary_name"] = ""
        self.partial_text = " ".join([x.spelling for x in node.get_tokens()])
        self._template_decl_params = []
        self._class_arglist = []
        return

    def add_template_decl_param(self, kind: int, ptype: str, name: str) -> None:
        ptype_use = ptype.replace(' ', '')
        name_use = name.replace(' ', '')
        self._template_decl_params.append((kind, ptype_use, name_use))
        return

    def process_template_paramlist(self, paramlist) -> None:
        pmatches = split_bracketed_list(paramlist)
        for pmatch in pmatches:
            tmatch = re_type_param.match(pmatch)
            ntmatch = re_nontype_param.match(pmatch)
            if tmatch is not None:
                tmatch_groupdict = tmatch.groupdict()
                if "template_def" in tmatch_groupdict and \
                        tmatch_groupdict["template_def"] is not None:
                    self.add_template_decl_param("TEMPLATE", "#",
                            tmatch.group('name'))
                elif "name" in tmatch_groupdict and tmatch_groupdict["name"] is not None:
                    self.add_template_decl_param("TYPE", "#",
                            tmatch.group('name'))
            elif ntmatch is not None:
                self.add_template_decl_param("NONTYPE",
                        ntmatch.group('type'), ntmatch.group('name'))
        return

    def process_class_template_arglist(self, carglist) -> None:
        amatches = split_bracketed_list(carglist)
        for amatch in amatches:
            self._class_arglist.append(amatch.replace(' ', ''))
        return

    def parse_template_decl(self) -> None:
        tmatch = re_template_decl.search(self.partial_text)
        self.process_template_paramlist(tmatch.group('t_arglist'))
        cmatch = None
        if not self["is_alias"]:
            cmatch = re_template_class.search(self.partial_text)
        else:
            cmatch = re_template_alias.search(self.partial_text)
        if cmatch is not None:
            self["primary_name"] = cmatch.group('cls_name')
            if "t_arglist" in cmatch.groupdict() and cmatch.groupdict()["t_arglist"] is not None:
                self.process_class_template_arglist(cmatch.group('t_arglist'))

        for pidx, param in enumerate(self._class_arglist):
            for tparam in self._template_decl_params:
                if param == tparam[2]:
                    self._class_arglist[pidx] = "#"
        return

    def extract_params(self) -> typing.Tuple[str]:
        return tuple((arg for arg in self._class_arglist))

    @if_handle
    def handle(self, node: cindex.Cursor) -> 'PartialSpecializationObject':
        TemplateObject.handle(self, node)
        if not self["is_alias"]:
            ParseObject.handle(self, node)
        self.parse_template_decl()
        self["partial_ref"] = \
                self["header"].header_match_template_ref(self["primary_name"], self.extract_params())
        self["dependencies"].append(self["partial_ref"])
        return self



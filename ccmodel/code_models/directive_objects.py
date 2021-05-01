from clang import cindex, enumerations
import typing
import abc
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from ..rules import code_model_map as cmm
from ..utils.code_utils import replace_template_params_str


class DirectiveObject(ParseObject, metaclass=abc.ABCMeta):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        ParseObject.__init__(self, node, force)
        self.info["directive"] = ""
        self.do_name_check = False
        return

    @abc.abstractmethod
    def handle(self, node: cindex.Cursor) -> "DirectiveObject":
        pass

    def get_directive(self) -> str:
        return self.directive_prefix + self.directive + ";"

    def set_names(self) -> None:

        self["directive"] = self.directive_prefix + self["directive"]
        self["directive"] = replace_template_params_str(
                self["directive"],
                self["template_parents"]
                )
        self["id"] = self["directive"]
        self["id"] = replace_template_params_str(
                self["directive"],
                self["template_parents"]
                )
        self["scoped_id"] = (
            ":" + self.directive_prefix.rstrip().upper() + ":" + self["directive"]
        )
        if self["scope"]["scoped_id"] != "":
            self["scoped_id"] = self["scope"]["scoped_id"] + self["scoped_id"]
        
        self["scoped_displayname"] = (
            ":" + self.directive_prefix.rstrip().upper() + ":" + self["directive"]
        )
        if self["scope"]["scoped_displayname"] != "":
            self["scoped_displayname"] = (
                self["scope"]["scoped_displayname"] + self["scoped_displayname"]
            )
        self["scoped_id"] = self["scoped_id"].replace("GlobalNamespace", "")
        self["scoped_displayname"] = self["scoped_displayname"].replace(
            "GlobalNamespace", ""
        )

        self["scoped_id"] = replace_template_params_str(
                self["scoped_id"],
                self["template_parents"]
        )

        self["scoped_displayname"] = replace_template_params_str(
                self["scoped_displayname"],
                self["template_parents"]
        )

        self["usr"] = self["scoped_displayname"]

        return

    def set_scope(self, scope: "ParseObject") -> "DirectiveObject":
        self["scope"] = scope
        return self


@cmm.default_code_model(cindex.CursorKind.USING_DIRECTIVE)
class UsingNamespaceObject(DirectiveObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        DirectiveObject.__init__(self, node, force)
        self.directive_prefix = "using namespace "
        self.info["using_namespace"] = "" 
        self.info["id"] = self.directive_prefix
        return

    def process_child(self, child: cindex.Cursor, set_names: bool = True) -> None:
        children = []
        self.extend_children(child, children)
        for child in self.children(children, cindex.CursorKind.NAMESPACE_REF):
            self["directive"] = (
                    child.spelling
                    if self["directive"] == ""
                    else self["directive"] + "::" + child.spelling
            )
        self["using_namespace"] = self["directive"]
        self.determine_scope_name(child)
        if set_names:
            self.set_names()
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "UsingNamespaceObject":
        self.process_child(node)
        ParseObject.handle(self, node)
        return self


@cmm.default_code_model(cindex.CursorKind.USING_DECLARATION)
class UsingDeclarationObject(DirectiveObject):
    def __init__(self, node: typing.Optional[cindex.Cursor] = None, force: bool = False):
        DirectiveObject.__init__(self, node, force)
        self.directive_prefix = "using "
        self.info["using_type"] = ""
        self.info["type_name"] = ""
        return

    def process_child(self, node: cindex.Cursor, set_names: bool = True) -> None:
        children = []
        self.extend_children(node, children)
        for child in self.children(children, cindex.CursorKind.NAMESPACE_REF):
            self["directive"] = (
                    child.spelling
                    if self["directive"] == ""
                    else self["directive"] + "::" + child.spelling
            )
        for child in [
            x for x in node.get_children() if x.kind != cindex.CursorKind.NAMESPACE_REF
        ]:
            self["directive"] = (
                child.spelling
                if self["directive"] == ""
                else self["directive"] + "::" + child.spelling
            )
        self["using_type"] = self["directive"]
        self["type_name"] = self["directive"].split("::")[-1]
        self.determine_scope_name(child)
        if set_names:
            self.set_names()
        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "UsingDeclarationObject":
        self.process_child(node)
        ParseObject.handle(self, node)
        return self

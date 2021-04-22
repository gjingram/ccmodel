from clang import cindex, enumerations
import typing
import abc
import pdb

from .decorators import if_handle, append_cpo
from .parse_object import ParseObject
from ..rules import code_model_map as cmm

class DirectiveObject(ParseObject, metaclass=abc.ABCMeta):

    def __init__(self, node: cindex.Cursor, force: bool = False):
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
        self["id"] = self["directive"]
        self["scoped_id"] = ":" + self.directive_prefix.rstrip().upper() + ":" + \
                self["directive"]
        if self["scope"]["scoped_id"] != "":
            self["scoped_id"] = self["scope"]["scoped_id"] + self["scoped_id"]
        self["scoped_displayname"] = ":" + self.directive_prefix.rstrip().upper() + ":" + \
                self["directive"]
        if self["scope"]["scoped_displayname"] != "":
            self["scoped_displayname"] = self["scope"]["scoped_displayname"] + \
                    self["scoped_displayname"]
        self["scoped_id"] = self["scoped_id"].replace("GlobalNamespace", "")
        self["scoped_displayname"] = self["scoped_displayname"].replace("GlobalNamespace", "")


        return

    def set_scope(self, scope: "ParseObject") -> "DirectiveObject":
        self["scope"] = scope
        self.set_names()
        return self


@cmm.default_code_model(cindex.CursorKind.USING_DIRECTIVE)
class UsingNamespaceObject(DirectiveObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        DirectiveObject.__init__(self, node, force)

        self.directive_prefix = "using namespace "
        children = []
        self.extend_children(node, children)

        for child in self.children(children, cindex.CursorKind.NAMESPACE_REF):
            self["directive"] = child.spelling if self["directive"] == "" \
                    else self["directive"] + "::" + child.spelling

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "UsingNamespaceObject":
        ParseObject.handle(self, node)
        self.determine_scope_name(node)
        return self


@cmm.default_code_model(cindex.CursorKind.USING_DECLARATION)
class UsingDeclarationObject(DirectiveObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        DirectiveObject.__init__(self, node, force)

        children = []
        self.extend_children(node, children)
        self.directive_prefix = "using "

        for child in self.children(children, cindex.CursorKind.NAMESPACE_REF):
            self["directive"] = child.spelling if self["directive"] == "" else \
                    self["directive"] + "" + child.spelling

        for child in [x for x in node.get_children() if x.kind != cindex.CursorKind.NAMESPACE_REF]:
            self["directive"] = child.spelling if self["directive"] == "" else \
                    self["directive"] + "::" + child.spelling

        return

    @if_handle
    def handle(self, node: cindex.Cursor) -> "UsingDeclarationObject":
        ParseObject.handle(self, node)
        self.determine_scope_name(node)
        return self

from clang import cindex, enumerations
import typing
import abc
import pdb

from illuminate.code_models.decorators import if_handle, append_cpo
from illuminate.code_models.parse_object import ParseObject
import illuminate.rules.code_model_map as cmm

class DirectiveObject(ParseObject, metaclass=abc.ABCMeta):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        ParseObject.__init__(self, node, force)
       
        self.do_name_check = False
        self.directive = ""
        self.directive_prefix = ""

        return

    @abc.abstractmethod
    def handle(self, node: cindex.Cursor) -> "DirectiveObject":
        pass

    def get_directive(self) -> str:
        return self.directive_prefix + self.directive + ";"

    def set_names(self) -> None:

        self.directive = self.directive_prefix + self.directive
        self.id = self.directive
        self.qualified_id = self.scope.qualified_id + ":" + self.directive_prefix.rstrip().upper() + ":" + \
                self.directive
        self.qualified_id = self.qualified_id.replace("GlobalNamespace:", "")
        if self.qualified_id[0] == ":":
            self.qualified_id = self.qualified_id[1:]

        return

    def set_scope(self, scope: "ParseObject") -> "ParseObject":
        self.scope = scope
        self.set_names()
        return self


@cmm.default_code_model(cindex.CursorKind.USING_DIRECTIVE)
class UsingNamespaceObject(DirectiveObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        DirectiveObject.__init__(self, node, force)

        self.directive_prefix = "using namespace "

        for child in [x for x in node.get_children() if x.kind == cindex.CursorKind.NAMESPACE_REF]:
            self.directive = child.spelling if self.directive == "" else self.directive + "::" + child.spelling

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> "UsingNamespaceObject":
        ParseObject.handle(self, node)
        return self

    def get_qualified_id(self) -> None:
        return


@cmm.default_code_model(cindex.CursorKind.USING_DECLARATION)
class UsingDeclarationObject(DirectiveObject):

    def __init__(self, node: cindex.Cursor, force: bool = False):
        DirectiveObject.__init__(self, node, force)

        self.directive_prefix = "using "

        for child in [x for x in node.get_children() if x.kind == cindex.CursorKind.NAMESPACE_REF]:
            self.directive = child.spelling if self.directive == "" else self.directive + "" + child.spelling

        for child in [x for x in node.get_children() if x.kind != cindex.CursorKind.NAMESPACE_REF]:
            self.directive = child.spelling if self.directive == "" else self.directive + "::" + child.spelling

        return

    @if_handle
    @append_cpo
    def handle(self, node: cindex.Cursor) -> "UsingDeclarationObject":
        ParseObject.handle(self, node)
        return self

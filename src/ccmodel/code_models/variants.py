from .basic import (
    JsonWrapper,
    Include,
    Variant,
    SkippableVariant,
    Name,
    SourceRange,
    SourceLocation,
    register_ptr
)
import ccmodel.code_models.pointers as pointers
from ccmodel.utils.code_utils import (
        split_id,
        form_id,
        get_bracketed_list_items
        )
from typing import Optional
import copy

################################# attrs #######################################


class AttrPointer(pointers.Pointer):

    def __init__(self, ptr: int, obj: "Variant"):
        super().__init__(ptr, obj)
        self._factory = AttrFactory
        return


class VersionTuple(Variant):

    def __init__(self):
        super().__init__()
        self.major = None
        self.minor = None
        self.subminor = None
        self.build = None
        return

    def load_content(self, obj: dict) -> dict:
        self.major = obj["major"]
        self.minor = obj["minor"]
        self.subminor = obj["subminor"]
        self.build = obj["build"]
        return obj


class Attribute(Variant):

    def __init__(self):
        super().__init__()
        self.pointer = -1
        self.location = None
        self.attr = None
        return

    def load_content(self, obj: dict) -> dict:
        self.pointer = register_ptr(obj["pointer"], self)
        self.location = SourceRange.load_json(obj["location"])
        self.attr = obj["attr"]
        return


class VisibilityAttr(Attribute):

    def __init__(self):
        super().__init__()
        self.kind = ""
        return

    def load_content(self, obj: dict) -> dict:
        Attribute.load_content(self, obj["attr"])
        self.kind = obj["kind"]
        return obj


class AnnotateAttr(Attribute):

    def __init__(self):
        super().__init__()
        self.annotation = ""
        return

    def load_content(self, obj: dict) -> dict:
        return obj


class AvailabilityAttr(Attribute):

    def __init__(self):
        super().__init__()
        self.platform = ""
        self.introduced = ""
        return

    def load_content(self, obj: dict) -> dict:
        Attribute.load_content(self, obj["attr"])
        self.platform = obj["platform"]
        self.introduced = obj["introduced"]
        return obj


class SentinelAttr(Attribute):

    def __init__(self):
        super().__init__()
        self.sentinel = None
        self.null_pos = None
        return

    def load_content(self, obj: dict) -> dict:
        Attribute.load_content(self, obj["attr"])
        self.sentinel = obj["sentinel"]
        self.null_pos = obj["null_pos"]
        return obj


class AttrFactory(object):

    def create_variant(
            obj: dict,
            save: bool = True,
            parent: Optional["Variant"] = None) -> "Attribute":

        if obj is None:
            return None

        out = None
        variant = obj["kind"]
        content = obj["content"]

        if content["skipped"]:
            out = SkippableVariant.load_json(content)
        if variant == "AvailabilityAttr":
            out = AvailabilityAttr.load_json(content)
        elif variant == "SentinelAttr":
            out = SentinelAttr.load_json(content)
        elif variant == "AnnotateAttr":
            out = AnnotateAttr.load_json(content)
        elif variant == "VisibilityAttr":
            out = VisibilityAttr.load_json(content)
        else:
            return None

        out.clang_kind = obj["clang_kind"]
        out.kind = variant
        out._json = obj
        out._save = save
        out._parent = parent

        return out


################################# types #######################################

integer_type_widths = {
        "char_type": -1,
        "short_type": -1,
        "int_type": -1,
        "long_type": -1,
        "longlong_type": -1
}


class TypePointer(pointers.Pointer):

    def __init__(self, ptr: int, obj: "Variant"):
        super().__init__(ptr, obj)
        self._factory = TypeFactory
        return


class Type(Variant):

    def __init__(self):
        super().__init__()
        self.pointer = -1
        self.desugared_type = None
        return

    def load_content(self, obj: dict) -> dict:
        self.pointer = register_ptr(obj["pointer"], self)
        self.desugared_type = TypePointer(obj["desugared_type"], self)
        return obj

    def resolve_type(self) -> str:
        pass

    def resolve_short_type(self) -> str:
        pass


class QualType(Variant):

    def __init__(self):
        super().__init__()
        self.type_object = -1
        self.type = ""
        self.canonical = None
        self.is_const = False
        self.is_volatile = False
        self.is_restrict = False
        pointers.qual_types.append(self)
        return

    def load_content(self, obj: dict) -> dict:
        self.kind = "QualType"
        self.type_object = TypePointer(obj["type_pointer"], self)
        self.type = obj["type"]
        self.canonical = obj["canonical"]
        self.is_const = obj["is_const"]
        self.is_restrict = obj["is_restrict"]
        self.is_volatile = obj["is_volatile"]

        if (
                self.type not in pointers.short_types and
                len(self.type) > len(self.canonical) and
                "type-parameter" not in self.type
            ):
            pointers.short_types[self.type] = self.canonical
            new_short_type = True
        if (
                self.canonical not in pointers.short_types and
                len(self.canonical) > len(self.type) and
                "type-parameter" not in self.canonical
            ):
            pointers.short_types[self.canonical] = self.type
        self.replace_short_type()

        return obj

    def resolve_type(self) -> str:
        return self.resolve_short_type()

    def resolve_short_type(self) -> str:
        if self.type in pointers.short_types:
            return pointers.short_types[self.type]
        elif self.canonical in pointers.short_types:
            return pointers.short_types[self.canonical]
        else:
            return self.type

    def replace_short_type(self) -> None:
        if (
                self.type in pointers.short_types and
                len(self.canonical) < len(pointers.short_types[self.type])
            ):
            pointers.short_types[self.type] = self.canonical
        if (
                self.canonical in pointers.short_types and
                len(self.type) < len(pointers.short_types[self.canonical])
            ):
            pointers.short_types[self.canonical] = self.type
        return

class BasicType(Type):

    def __init__(self):
        super().__init__()
        self.qual_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.qual_type = QualType.load_json(obj["qual_type"], parent=self)
        return obj

    def resolve_type(self) -> str:
        return self.qual_type.resolve_type()


class AdjustedType(BasicType):

    def __init__(self):
        super().__init__()
        return


class ArrayType(Type):

    def __init__(self):
        super().__init__()
        self.element_type = None
        self.stride = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.element_type = QualType.load_json(
                obj["element_type"],
                parent=self)
        self.stride = obj["stride"]
        return obj


class ConstantArrayType(ArrayType):

    def __init__(self):
        super().__init__()
        self.size = -1
        return

    def load_content(self, obj: dict) -> dict:
        ArrayType.load_content(self, obj["array_type"])
        self.size = obj["size"]
        return obj

    def resolve_type(self) -> str:
        return self.element_type + f"[{self.size}]"


class VariableArrayType(ArrayType):

    def __init__(self):
        super().__init__()
        self.pointer = -1
        return

    def load_content(self, obj: dict) -> dict:
        ArrayType.load_content(self, obj["array_type"])
        self.pointer = register_ptr(obj["pointer"], self)
        return obj

    def resolve_type(self) -> str:
        return ArrayType.resolve_type(self)


class AtomicType(BasicType):

    def __init__(self):
        super().__init__()
        return


class AttributedType(Type):

    def __init__(self):
        super().__init__()
        self.attr_kind = ""
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.attr_kind = obj["attr_kind"]
        return obj

    def resolve_type(self) -> str:
        return None


class BlockPointerType(BasicType):

    def __init__(self):
        super().__init__()
        self.type_name = ""
        return


class BuiltinType(Type):

    def __init__(self):
        super().__init__()
        self.type_name = ""
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.type_name = obj["type_name"]
        return obj

    def resolve_type(self) -> str:
        return self.type_name


class DecltypeType(BasicType):

    def __init__(self):
        super().__init__()
        return


class FunctionType(Type):

    def __init__(self):
        super().__init__()
        self.return_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.return_type = QualType.load_json(obj["return_type"], parent=self)
        return obj

    def resolve_type(self) -> str:
        return self.return_type.resolve_type()


class FunctionProtoType(FunctionType):

    def __init__(self):
        super().__init__()
        self.param_types = []
        return

    def load_content(self, obj: dict) -> dict:
        FunctionType.load_content(self, obj["function_type"])
        self.param_types = [
                QualType.load_json(x, parent=self) for x in obj["param_types"]
                ]
        return obj

    def resolve_type(self) -> str:
        out = FunctionType.resolve_type(self)
        parm_types = []
        for parm_type in self.param_types:
            parm_types.append(parm_type.resolve_type())
        out += "(" + ", ".join(parm_types) + ")"
        return out


class MemberPointerType(BasicType):

    def __init__(self):
        super().__init__()
        return


class ParenType(BasicType):

    def __init__(self):
        super().__init__()
        return


class PointerType(BasicType):

    def __init__(self):
        super().__init__()
        return


class ReferenceType(BasicType):

    def __init__(self):
        super().__init__()
        return


class TagType(Type):

    def __init__(self):
        super().__init__()
        self.decl = -1
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.decl = DeclPointer(obj["decl_pointer"], self)
        return obj

    def resolve_type(self) -> str:
        if self.decl.skipped:
            return "::".join(reversed(self.decl.id.qual_name))
        return (
                self.decl.type.resolve_type()
                )


class TypedefType(Type):

    def __init__(self):
        super().__init__()
        self.child_type = None
        self.decl = -1
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.child_type = QualType.load_json(
                obj["child_type"],
                parent=self)
        self.decl = DeclPointer(obj["decl_pointer"], self)
        return obj

    def resolve_type(self) -> str:
        if self.decl.skipped:
            return "::".join(reversed(self.decl.id.qual_name))

        return self.decl.underlying_type.type


class TemplateTypeParmType(Type):

    def __init__(self):
        super().__init__()
        self.id = ""
        self.depth = -1
        self.index = -1
        self.variadic = False
        self.parameter = -1
        self.desugared_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.id = obj["id"]
        self.depth = obj["depth"]
        self.index = obj["index"]
        self.is_pack = obj["is_pack"]
        self.parameter = DeclPointer(obj["parameter"], self)
        self.desugared_type = QualType.load_json(
                obj["desugared_type"],
                parent=self
                )
        return

    def resolve_type(self) -> str:
        if self.parameter.skipped:
            return "::".join(reversed(self.parameter.id.qual_name))
        return self.id


class SubstTemplateTypeParmType(Type):

    def __init__(self):
        super().__init__()
        self.replaced = -1
        self.replacement_type = None
        self.desugared_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.replaced = obj["replaced"]
        self.replacement_type = QualType.load_json(
                obj["replacement_type"],
                parent=self)
        self.desugared_type = QualType.load_json(
                obj["desugared_type"],
                parent=self
                )
        return obj

    def resolve_type(self) -> str:
        return self.replacement_type.resolve_type()


class TemplateSpecializationType(Type):

    def __init__(self):
        super().__init__()
        self.type_alias = False
        self.template_decl = -1
        self.aliased_type = None
        self.desugared_type = None
        self.specialization_args = []
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.type_alias = obj["type_alias"]
        self.template_decl = DeclPointer(obj["template_decl"], self)
        self.aliased_type = QualType.load_json(
                obj["aliased_type"],
                parent=self
                )
        self.desugared_type = QualType.load_json(
                obj["desugared_type"],
                parent=self
                )
        self.specialization_args = [
                TemplateArgument.load_json(x, parent=self) for x in
                obj["specialization_args"]
                ]
        return obj

    def resolve_type(self) -> str:
        if self.template_decl.skipped:
            out = "::".join(reversed(self.template_decl.qual_name))
        else:
            out = self.template_decl.get_qualified_id()
        args = []
        for arg in self.specialization_args:
            args.append(arg.type.resolve_type())
        out += "<" + ", ".join(args) + ">"
        return out


class InjectedClassNameType(Type):

    def __init__(self):
        super().__init__()
        self.injected_specialization_type = None
        self.desugared_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.injected_specialization_type = (
                QualType.load_json(
                    obj["injected_specialization_type"],
                    parent=self)
                )
        self.desugared_type = QualType.load_json(
                obj["desugared_type"],
                parent=self
                )
        return obj

    def resolve_type(self) -> str:
        return self.injected_specialization_type.resolve_type()


class DependentNameType(Type):

    def __init__(self):
        Type.__init__(self)
        self.identifier = ""
        self.desugared_type = None
        return

    def load_content(self, obj: dict) -> dict:
        Type.load_content(self, obj["type"])
        self.identifier = obj["identifier"]
        self.desugared_type = QualType.load_json(
                obj["desugared_type"],
                parent=self
                )
        return obj

    def resolve_type(self) -> str:
        return self.desugared_type.resolve_type()


class TypeFactory(object):

    def create_variant(
            type_obj: dict,
            parent: Optional["Variant"] = None) -> "Type":

        if type_obj is None:
            return None

        out = None
        variant = type_obj["kind"]
        content = type_obj["content"]

        if content["skipped"]:
            out = SkippableVariant.load_json(content)
        if variant == "AdjustedType":
            out = AdjustedType.load_json(content)
        elif variant == "ArrayType":
            out = ArrayType.load_json(content)
        elif variant == "ConstantArrayType":
            out = ConstantArrayType.load_json(content)
        elif variant == "VariableArrayType":
            out = VariableArrayType.load_json(content)
        elif variant == "AtomicType":
            out = AtomicType.load_json(content)
        elif variant == "AttributedType":
            out = AttributedType.load_json(content)
        elif variant == "BlockPointerType":
            out = BlockPointerType.load_json(content)
        elif variant == "BuiltinType":
            out = BuiltinType.load_json(content)
        elif variant == "DecltypeType":
            out = DecltypeType.load_json(content)
        elif variant == "FunctionType":
            out = FunctionType.load_json(content)
        elif variant == "FunctionProtoType":
            out = FunctionProtoType.load_json(content)
        elif variant == "MemberPointerType":
            out = MemberPointerType.load_json(content)
        elif variant == "PointerType":
            out = PointerType.load_json(content)
        elif variant == "ReferenceType":
             out = ReferenceType.load_json(content)
        elif variant == "TagType":
            out = TagType.load_json(content)
        elif variant == "TypedefType":
            out = TypedefType.load_json(content)
        elif variant == "TemplateTypeParmType":
            out = TemplateTypeParmType.load_json(content)
        elif variant == "SubstTemplateTypeParmType":
            out = SubstTemplateTypeParmType.load_json(content)
        elif variant == "TemplateSpecializationType":
            out = TemplateSpecializationType.load_json(content)
        elif variant == "InjectedClassNameType":
            out = InjectedClassNameType.load_json(content)
        elif variant == "DependentNameType":
            out = DependentNameType.load_json(content)
        elif variant == "RecordType":
            out = TagType.load_json(content)
        elif variant == "EnumType":
            out = TagType.load_json(content)
        elif variant == "LValueReferenceType":
            out = BasicType.load_json(content)
        elif variant == "RValueReferenceType":
            out = BasicType.load_json(content)
        elif variant == "DependentSizedArrayType":
            out = ArrayType.load_json(content)
        elif variant == "IncompleteArrayType":
            out = ArrayType.load_json(content)
        elif variant == "ParenType":
            out = BasicType.load_json(content)
        else:
            out = Type.load_json(content)

        out.clang_kind = type_obj["clang_kind"]
        out.kind = variant
        out._save = True
        out._json = type_obj
        out._parent = parent

        return out


################################# decls #######################################


class DeclPointer(pointers.Pointer):

    def __init__(self, ptr: int, obj: "Variant"):
        super().__init__(ptr, obj)
        self._factory = DeclFactory
        return


class StmtPointer(pointers.Pointer):

    def __init__(self, ptr: int, obj: "Variant"):
        super().__init__(ptr, obj)
        self._factory = StmtFactory
        return


class Stmt(Variant):

    def __init__(self):
        super().__init__()
        self.stmt = None
        self.pointer = -1
        self.location = None
        self.content = []
        return

    def load_content(self, obj: dict) -> dict:
        self.pointer = register_ptr(obj["pointer"], self)
        self.location = SourceRange.load_json(obj["location"])
        self.content = [
                StmtFactory.create_variant(stmt, save=False, parent=self) for 
                stmt in obj["content"]
                ]
        for obj in [x for x in self.content if x is not None]:
            obj.parent(self)
        return obj


class FullComment(Variant):

    def __init__(self):
        super().__init__()
        self.parent_pointer = -1
        self.location = None
        self.text = ""
        return

    def load_content(self, obj: dict) -> dict:
        self.parent_pointer = register_ptr(obj["parent_pointer"], self)
        self.location = SourceRange.load_json(obj["location"])
        self.text = obj["text"]
        return obj


class DeclStmt(Stmt):

    def __init__(self):
        super().__init__()
        self.decls = []
        return

    def load_content(self, obj: dict) -> dict:
        Stmt.load_content(self, obj["stmt"])
        for decl in obj["decls"]:
            obj = DeclFactory.create_variant(
                    decl,
                    save=False,
                    parent=self
                    )
            if obj is not None:
                self.decls.append(obj)
                obj.parent(self)
        return obj


class IdContainer(object):

    def __init__(self):
        super().__init__()
        self._named_decls = []
        self._identifier_map = {}
        return

    def __getitem__(self, iden: str) -> Variant:
        try:
            return self._identifier_map[iden]
        except KeyError:
            return None

    def ls(self, ilevel: int = 0) -> None:
        lead_char = "|-" if ilevel else "-"
        indent = f"{4 * ilevel * ' '}"
        ccm_id = self._local_ccm_identifier
        print(f"{indent}{lead_char} {ccm_id}: {type(self).__name__}")
        for iden, variant in self._identifier_map.items():
            if iden == ccm_id:
                continue
            if isinstance(variant, IdContainer):
                variant.ls(ilevel + 1)
                continue
            indent = f"{4 * (ilevel+1) * ' '}"
            print(f"{indent}|- {iden}: {type(variant).__name__}")
        return

    def build_id_map(self) -> None:
        for ndecl in self._named_decls:
            ndecl.set_ccm_identifier()
            self._identifier_map[ndecl._local_ccm_identifier] = ndecl
        return


class Decl(SkippableVariant):

    def __init__(self):
        super().__init__()
        self.pointer = -1
        self.parent = None
        self.location = None
        self.owning_module = None
        self.is_hidden = False
        self.is_implicit = False
        self.is_used = False
        self.is_this_declaration_referenced = False
        self.is_invalid_decl = False
        self.attributes = []
        self.full_comment = None
        self.access_spec = None
        return

    def load_content(self, obj: dict) -> None:
        if SkippableVariant.load_content(self, obj):
            return
        self.pointer = register_ptr(obj["pointer"], self)
        self.parent = DeclPointer(obj["parent_pointer"], self)
        self.location = SourceRange.load_json(obj["location"])
        self.owning_module = obj["owning_module"]
        self.is_hidden = obj["is_hidden"]
        self.is_implicit = obj["is_implicit"]
        self.is_used = obj["is_used"]
        self.is_this_declaration_referenced = obj["is_this_declaration_referenced"]
        self.is_invalid_decl = obj["is_invalid_decl"]
        for attr in obj["attributes"]:
            attr_obj = AttrFactory.create_variant(
                    JsonWrapper(attr),
                    save=False,
                    parent=self)
            if attr_obj is not None:
                self.attributes.append(attr_obj)
        self.full_comment = FullComment.load_json(
                obj["full_comment"],
                parent=self
                )
        return


class NamedDecl(Decl, Name):

    def __init__(self):
        super().__init__()
        self._ccm_identifier = ""
        self._local_ccm_identifier = ""
        return

    def load_content(self, obj: dict) -> dict:
        Decl.load_content(self, obj["decl"])
        Name.load_content(self, obj["id"])
        return obj

    def get_qualified_id(self) -> str:
        return Name.write_qual_name(self)

    def get_id(self) -> str:
        return Name.write_name(self)

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        self._local_ccm_identifier = self.name
        if self._parent and "_ccm_identifier" in vars(self._parent):
            if self._parent._ccm_identifier == "":
                self._parent.set_ccm_identifier()
            self._ccm_identifier = "::".join(
                    [
                        self._parent._ccm_identifier,
                        self._local_ccm_identifier
                        ]
                    )
        else:
            self._ccm_identifier = "::".join(reversed(self.qual_name))
        return


class DeclRef(SkippableVariant):

    def __init__(self):
        super().__init__()
        self.decl = -1
        self.id = None
        self.is_hidden = False
        self.qual_type = None
        return

    def load_content(self, obj: dict) -> None:
        if SkippableVariant.load_content(self, obj):
            return
        self.kind = "DeclRef"
        self.decl = DeclPointer(obj["decl_pointer"], self)
        self.id = obj["id"]
        self.is_hidden = obj["is_hidden"]
        self.qual_type = QualType.load_json(obj["qual_type"], parent=self)
        return


class NestedNameSpecifierLoc(Variant):

    def __init__(self):
        super().__init__()
        self.kind = ""
        self.ref = None
        return

    def load_content(self, obj: dict) -> dict:
        self.kind = obj["kind"]
        self.ref = DeclRef.load_json(obj["ref"], parent=self)
        return obj


class LambdaCapture(Variant):

    def __init__(self):
        super().__init__()
        self.capture_kind = ""
        self.captures_this = False
        self.captures_variable = False
        self.captures_VLAtype = False
        self.init_captured_vardecl = None
        self.captured_var = None
        self.is_implicit = False
        self.location = None
        self.is_pack_expansion = False
        return

    def load_content(self, obj: dict) -> dict:
        self.capture_kind = obj["capture_kind"]
        self.captures_this = obj["captures_this"]
        self.captures_variable = obj["captures_variable"]
        self.captures_VLAType = obj["captures_VLAType"]
        self.init_captured_vardecl = DeclFactory.create_variant(
                obj["init_captured_vardecl"],
                save=False,
                parent=self
                )
        self.captured_var = DeclRef.load_json(
                obj["captured_var"],
                parent=self
                )
        self.is_implicit = obj["is_implicit"]
        self.location = SourceRange(
                obj["location"]
                )
        self.is_pack_expansion = obj["is_pack_expansion"]
        return obj


class CXXCtorInitializer(Variant):

    def __init__(self):
        super().__init__()
        self.declaration = None
        self.qualified_type = -1
        self.virtual_base = False
        self.init_expr = None
        return

    def load_content(self, obj: dict) -> dict:
        self.kind = obj["kind"]
        self.declaration = DeclRef.load_json(obj["declaration"], parent=self)
        self.qualified_type = TypePointer(obj["qualified_type"], self)
        self.virtual_base = obj["virtual_base"]
        self.init_expr = StmtFactory.create_variant(obj["init_expr"])
        return obj


class DeclContext(SkippableVariant, IdContainer):

    def __init__(self):
        super().__init__()
        self.c_linkage = False
        self.has_external_lexical_storage = None
        self.has_external_visible_storage = None
        self.declarations = []
        self.context_pointer = -1
        self.n_anonymous_fields = 0
        self.n_anonymous_enums = 0
        self.n_anonymous_namespaces = 0
        self.n_anonymous_unions = 0
        return

    def load_content(self, obj: dict) -> dict:
        if SkippableVariant.load_content(self, obj):
            return
        self.c_linkage = obj["c_linkage"]
        self.has_external_lexical_storage = (
                obj["has_external_lexical_storage"]
                )
        self.has_external_visible_storage = (
                obj["has_external_visible_storage"]
                )
        for decl in obj["declarations"]:
            decl_obj = DeclFactory.create_variant(
                    JsonWrapper(decl),
                    save=False,
                    parent=self)
            if decl_obj is not None:
                self.declarations.append(decl_obj)
            if isinstance(decl_obj, NamedDecl):
                self._named_decls.append(decl_obj)
        self.context_pointer = obj["pointer"]

        return obj


class CapturedDecl(Decl, DeclContext):

    def __init__(self):
        super().__init__()
        return

    def load_content(self, obj: dict) -> dict:
        Decl.load_content(self, obj["decl"])
        DeclContext.load_content(self, obj["content"])
        return obj


class LinkageSpecDecl(Decl, DeclContext):

    def __init__(self):
        super().__init__()
        return

    def load_content(self, obj: dict) -> dict:
        Decl.load_content(self, obj["decl"])
        DeclContext.load_content(self, obj["context"])
        return obj


class NamespaceDecl(NamedDecl, DeclContext):

    def __init__(self):
        super().__init__()
        self.is_inline = False
        self.original_namespace = None
        return

    def load_content(self, obj: dict) -> dict:
        NamedDecl.load_content(self, obj["named_decl"])
        DeclContext.load_content(self, obj["context"])
        self.is_inline = obj["is_inline"]
        self.original_namespace = obj["original_namespace"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        if self.name == "":
            self.name = (
            f"__anonymous_namespace{self._parent.n_anonymous_namespaces}"
            )
            self.qual_name[0] = self.name
            self._parent.n_anonymous_namespaces += 1
        NamedDecl.set_ccm_identifier(self)
        return


class TypeDecl(NamedDecl):

    def __init__(self):
        super().__init__()
        self.type = -1
        return

    def load_content(self, obj: dict) -> dict:
        NamedDecl.load_content(self, obj["named_decl"])
        self.type = TypePointer(obj["type_pointer"], self)
        return obj

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return


class TagDecl(TypeDecl, DeclContext):

    def __init__(self):
        super().__init__()
        self.tag_kind = ""
        return

    def load_content(self, obj: dict) -> dict:
        TypeDecl.load_content(self, obj["type_decl"])
        DeclContext.load_content(self, obj["context"])
        self.tag_kind = obj["tag_kind"]
        return obj


class ValueDecl(NamedDecl, QualType):

    def __init__(self):
        super().__init__()
        return

    def load_content(self, obj: dict) -> dict:
        NamedDecl.load_content(self, obj["named_decl"])
        QualType.load_content(self, obj["qualified_type"])
        return obj

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return


class TranslationUnitDecl(DeclContext):
    
    def __init__(self):
        super().__init__()
        self.referenced_decls = []
        self.referenced_types = []
        return

    def load_content(self, obj: dict) -> dict:
        DeclContext.load_content(self, obj["main_context"])
        self.integer_type_widths = obj["integer_type_widths"]
        for decl in obj["referenced_decls"]:
            self.referenced_decls.append(
                    DeclFactory.create_variant(
                        JsonWrapper(decl),
                        parent=self)
                    )
        for type_ in obj["referenced_types"]:
            self.referenced_types.append(
                    TypeFactory.create_variant(JsonWrapper(type_),
                        parent=self)
                    )
        self.pointer = register_ptr(obj["pointer"], self)
        return obj


class TypedefDecl(TypeDecl, IdContainer):

    def __init__(self):
        super().__init__()
        self.underlying_type = None
        self.is_module_private = False
        pointers.typedefs.append(self)
        return

    def load_content(self, obj: dict) -> dict:
        TypeDecl.load_content(self, obj["type_decl"])
        self.underlying_type = QualType.load_json(
                obj["underlying_type"],
                parent=self)
        self.is_module_private = obj["is_module_private"]
        return obj

    def link_typedef(self) -> None:
        if (
                "desugared_type" not in
                vars(self.underlying_type.type_object)
            ):
            return
        if self.underlying_type.type_object.desugared_type is None:
            return
        if (
                isinstance(
                    self.underlying_type.type_object.desugared_type,
                    TagType
                    ) and
                isinstance(
                    self.underlying_type.type_object.desugared_type.decl,
                    IdContainer
                    )
            ):
            self._identifier_map = copy.deepcopy(
                    self.underlying_type.type_object.desugared_type
                    .decl._identifier_map
                    )
            for decl in self._identifier_map.values():
                decl._parent = self
                decl.name = decl.name if decl.name != "" else self.name
                decl.qual_name = [
                        decl.name,
                        *self.qual_name
                        ]
                decl._ccm_identifier = ""
                decl.set_ccm_identifier()

        return


class EnumDecl(TagDecl):

    def _init__(self):
        super().__init__()
        self.scope = ""
        self.is_module_private = False
        return

    def load_content(self, obj: dict) -> dict:
        TagDecl.load_content(self, obj["tag_decl"])
        self.scope = obj["scope"]
        self.is_module_private = obj["is_module_private"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        id_parts = self.qual_name
        name = id_parts[0]
        anon_enum = any(["anonymous_enum" in x for x in id_parts])
        if anon_enum:
            id_parts = [
                    idp for idp in id_parts if
                    not "anonymous_enum" in
                    idp
                    ]
            self.name = f"__anonymous_enum{self._parent.n_anonymous_enums}"
            self.qual_name[0] = self.name
            self._parent.n_anonymous_enums += 1
            pointers.short_types[name] = self.name
        self._local_ccm_identifier = self.name
        self._ccm_identifier = self.get_qualified_id()
        return


class RecordDecl(TagDecl):

    def __init__(self):
        super().__init__()
        self.definition = -1
        self.is_module_private = False
        self.is_complete_definition = False
        self.is_dependent_type = False
        return

    def load_content(self, obj: dict) -> dict:
        TagDecl.load_content(self, obj["tag_decl"])
        self.definition = DeclPointer(obj["definition_pointer"], self)
        self.is_module_private = obj["is_module_private"]
        self.is_complete_definition = obj["is_complete_definition"]
        self.is_dependent_type = obj["is_dependent_type"]
        return obj


class EnumConstantDecl(ValueDecl):

    def __init__(self):
        super().__init__()
        self.init_expr = None
        self.value = None
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.init_expr = StmtFactory.create_variant(
                obj["init_expr"],
                save=False,
                parent=self
                )
        self.value = obj["value"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        id_parts = self.qual_name
        self._local_ccm_identifier = id_parts[0]
        self._ccm_identifier = "::".join(reversed(id_parts))
        self.name = id_parts[0]
        self.qual_name = id_parts[1:]
        return


class IndirectFieldDecl(ValueDecl):
    
    def __init__(self):
        super().__init__()
        self.decl_refs = []
        self.direct = None
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.decl_refs = [DeclRef.load_json(x, parent=self) for
                x in obj["decl_refs"]]
        self.direct = DeclPointer(
                self.decl_refs[-1].decl._pointer,
                self
                )
        return obj


class FunctionDecl(ValueDecl, IdContainer):

    def __init__(self):
        super().__init__()
        self.mangled_name = None
        self.is_cpp = False
        self.is_inline = False
        self.is_module_private = False
        self.is_pure = False
        self.is_delete_as_written = False
        self.is_no_return = False
        self.is_variadic = False
        self.is_static = False
        self.parameters = []
        self.decl_ptr_with_body = None
        self.body = None
        self.template_specialization = None
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.mangled_name = obj["mangled_name"]
        self.is_ccp = obj["is_cpp"]
        self.is_inline = obj["is_inline"]
        self.is_module_private = obj["is_module_private"]
        self.is_pure = obj["is_pure"]
        self.is_deleted_as_written = obj["is_deleted_as_written"]
        self.is_no_return = obj["is_no_return"]
        self.is_variadic = obj["is_variadic"]
        self.is_static = obj["is_static"]
        self.parameters = [
                DeclFactory.create_variant(
                    JsonWrapper(x),
                    save=False,
                    parent=self) for
                x in obj["parameters"]
                ]
        for param in [x for x in self.parameters if x is not None]:
            self._named_decls.append(param)

        self.template_specialization = (
                TemplateSpecialization.load_json(
                    obj["template_specialization"],
                    parent=self
                    )
                )
        if self.template_specialization is not None:
            self._named_decls.append(self.template_specialization)

        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        NamedDecl.set_ccm_identifier(self)
        self._local_ccm_identifier += self.get_arg_list()
        self._ccm_identifier += self.get_arg_list()
        return

    def get_arg_list(self) -> str:
        parms = []
        for parm in self.parameters:
            parm_repr = ""
            if (
                    isinstance(
                    parm.type_object,
                    BasicType) and
                    isinstance(
                        parm.type_object.qual_type.type_object,
                        TemplateTypeParmType
                        )
            ):
                parameter = parm.type_object.resolve_type()
                type_ = parm.type
                parm_repr = (
                        type_.replace(
                            parameter,
                            parm.type_object.qual_type.type_object.parameter\
                                    .parm_repr()
                                    )
                        )
            elif isinstance(parm.type_object, TemplateTypeParmType):
                parameter = parm.type_object.resolve_type()
                type_ = parm.type
                parm_repr = type_.replace(
                        parameter,
                        parm.type_object.parameter.parm_repr()
                        )
            else:
                parm_repr = parm.type

            parms.append(parm_repr)

        arg_list = "(" + ", ".join(parms) + ")"
        return arg_list


class FieldDecl(ValueDecl):

    def __init__(self):
        super().__init__()
        self.is_mutable = False
        self.is_module_private = False
        self.init_expr = None
        self.bit_width_expr = None
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.is_mutable = obj["is_mutable"]
        self.is_module_private = obj["is_module_private"]
        self.bit_width_expr = StmtFactory.create_variant(
                obj["bit_width_expr"],
                save=False,
                parent=self
                )

        self.init_expr = StmtFactory.create_variant(
                obj["init_expr"],
                save=False,
                parent=self
                )

        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        NamedDecl.set_ccm_identifier(self)
        self._local_ccm_identifier = self._local_ccm_identifier.replace(
                "__anon_field_",
                "__anonymous_field"
                )
        self._ccm_identifier = self._ccm_identifier.replace(
                "__anon_field_",
                "__anonymous_field"
                )
        return


class VarDecl(ValueDecl):

    def __init__(self):
        super().__init__()
        self.is_global = False
        self.is_extern = False
        self.is_static = False
        self.is_static_local = False
        self.is_static_data_member = False
        self.is_const_expr = False
        self.is_init_ice = False
        self.init_expr = None
        self.is_init_expr_cxx11_constant = False
        self.parm_index_in_function = None
        self.has_default = False
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.is_global = obj["is_global"]
        self.is_extern = obj["is_extern"]
        self.is_static = obj["is_static"]
        self.is_static_local = obj["is_static_local"]
        self.is_static_data_member = obj["is_static_data_member"]
        self.is_const_expr = obj["is_const_expr"]
        self.is_init_ice = obj["is_init_ice"]
        self.has_default = obj["has_default"]
        self.init_expr = StmtFactory.create_variant(
                obj["init_expr"],
                save=False,
                parent=self
                )

        self.is_init_expr_cxx11_constant = (
                obj["is_init_expr_cxx11_constant"]
                )
        self.parm_index_in_function = (
                obj["parm_index_in_function"]
                )
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        if self.name == "":
            self.name = f"__anonymous_field{self._parent.n_anonymous_fields}"
            self.qual_name[0] = self.name
            self._parent.n_anonymous_fields += 1
        NamedDecl.set_ccm_identifier(self)
        return


class ImportDecl(Decl):

    def __init__(self):
        super().__init__()
        self.module_name = ""
        return

    def load_content(self, obj: dict) -> dict:
        Decl.load_content(self, obj["decl"])
        self.module_name = obj["module_name"]
        return obj


class UsingDirectiveDecl(NamedDecl):

    def __init__(self):
        super().__init__()
        self.using_location = None
        self.namespace_key_location = None
        self.nested_name_specifier_locs = []
        self.nominated_namespace = None
        return

    def load_content(self, obj: dict) -> dict:
        NamedDecl.load_content(self, obj["named_decl"])
        self.using_location = SourceLocation.load_json(
                obj["using_location"]
                )
        self.namespace_key_location = SourceLocation.load_json(
                obj["namespace_key_location"]
                )
        self.nested_name_specifier_locs = [
                NestedNameSpecifierLoc.load_json(x, parent=self) 
                for x in obj["nested_name_specifier_locs"]
                ]
        self.nominated_namespace = (
                DeclRef.load_json(
                    obj["nominated_namespace"],
                    parent=self
                )
                )
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        self._ccm_identifier = "<using-directive "
        self._ccm_identifier += self.location.file
        self._ccm_identifier += (
                ":" +
                str(self.location.begin.line)
                + ">"
                )
        self._local_ccm_identifier = self._ccm_identifier
        return


class NamespaceAliasDecl(NamedDecl):

    def __init__(self):
        super().__init__()
        self.namespace_loc = None
        self.target_name_loc = None
        self.nested_name_specifier_locs = []
        self.namespace = None
        return

    def load_content(self, obj: dict) -> dict:
        NamedDecl.load_content(self, obj["named_decl"])
        self.namespace_loc = (
                SourceLocation.load_json(obj["namespace_loc"])
                )
        self.target_name_loc = (
                SourceLocation.load_json(obj["target_name_loc"])
                )
        self.nested_name_specifier_locs = [
                NestedNameSpecifierLoc.load_json(x, parent=self) for x in
                obj["nested_name_specifier_locs"]
                ]
        self.namespace = DeclRef.load_json(obj["namespace"], parent=self)
        return obj

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return


class ClassBase(Variant):

    def __init__(self):
        super().__init__()
        self.type = -1
        self.access_specifier = ""
        self.is_virtual = False
        self.is_transitive = False
        return

    def load_content(self, obj: dict) -> dict:
        self.type = TypePointer(obj["type"], self)
        self.access_specifier = obj["access_specifier"]
        self.is_virtual = obj["is_virtual"]
        self.is_transitive = obj["is_transitive"]
        return obj


class CXXRecordDecl(RecordDecl):
    
    def __init__(self):
        super().__init__()
        self.is_complete = False
        self.is_polymorphic = False
        self.is_abstract = False
        self.bases = []
        self.is_pod = False
        self.destructor = None
        self.lambda_call_operator = None
        self.lambda_captures = []
        self.is_struct = False
        self.is_interface = False
        self.is_class = False
        self.is_union = False
        self.is_enum = False
        return

    def load_content(self, obj: dict) -> dict:
        RecordDecl.load_content(self, obj["record"])
        self.is_complete = obj["is_complete"]
        self.is_polymorphic = obj["is_polymorphic"]
        self.is_abstract = obj["is_abstract"]
        self.bases = [
                ClassBase.load_json(x, parent=self) for x in obj["bases"]
                ]
        self.is_pod = obj["is_pod"]
        dtor_names = copy.copy(self.qual_name)
        dtor_names[0] = "~" + dtor_names[0]
        self.destructor = "::".join(reversed(dtor_names))
        self.destructor += "()"
        self.lambda_call_operator = (
                DeclRef.load_json(
                    obj["lambda_call_operator"],
                    parent=self
                    )
                )
        self.lambda_captures = [
                LambdaCapture.load_json(x, parent=self) for
                x in obj["lambda_captures"]
                ]
        self.is_struct = obj["is_struct"]
        self.is_interface = obj["is_interface"]
        self.is_class = obj["is_class"]
        self.is_union = obj["is_union"]
        self.is_enum = obj["is_enum"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        if self.is_union and self.name == "":
            anon_name = self.qual_name[0]
            self.name = f"__anonymous_union{self._parent.n_anonymous_unions}"
            self.qual_name[0] = self.name
            self._parent.n_anonymous_unions += 1
            pointers.short_types[anon_name] = (
                    self.get_qualified_id()
                    )
        NamedDecl.set_ccm_identifier(self)
        return


class TemplateArgument(Variant):

    def __init__(self):
        super().__init__()
        self.kind = ""
        self.type = None
        self.pointer = -1
        self.integer = None
        self.parameter_pack = []
        return

    def load_content(self, obj: dict) -> dict:
        self.kind = obj["kind"]
        self.type = QualType.load_json(obj["type"])
        self.pointer = DeclPointer(obj["pointer"], self)
        self.integer = obj["integer"]
        self.parameter_pack = [
                TemplateArgument.load_json(x, parent=self) for
                x in obj["parameter_pack"]]
        self.clang_kind = "TemplateArgument"
        self._json = obj
        return obj


class TemplateSpecialization(Variant, IdContainer):

    def __init__(self):
        super().__init__()
        self.template = -1
        self.specialization_args = []
        return

    def load_content(self, obj: dict) -> dict:
        self.template = DeclPointer(obj["template_decl"], self)
        self.specialization_args = [
                TemplateArgument.load_json(x, parent=self) for
                x in obj["specialization_args"]
                ]
        return obj


class ClassTemplateSpecializationDecl(CXXRecordDecl, TemplateSpecialization):

    def __init__(self):
        super().__init__()
        self.mangled_name = ""
        return

    def load_content(self, obj: dict) -> dict:
        CXXRecordDecl.load_content(self, obj["cxx_record"])
        TemplateSpecialization.load_content(self, obj["specialization"])
        self.mangled_name = obj["mangled_name"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        NamedDecl.set_ccm_identifier(self)
        ccm_id_parts = split_id(self._ccm_identifier)
        self._ccm_identifier = ccm_id_parts[0]
        arg_repr = (
                "<" +
                self.get_arglist_repr(self.specialization_args) +
                ">"
                )
        self._ccm_identifier += arg_repr
        self._local_ccm_identifier += arg_repr
        return

    def get_arglist_repr(self, args: list) -> str:
        arg_repr = []
        for arg in args:
            if arg.kind == "Type":
                if isinstance(
                        arg.type.type_object,
                        TemplateTypeParmType
                ):
                    if (
                            arg.type.type_object.variadic and
                            not arg.type.type_object.is_pack
                    ):
                        arg_repr.append("[#...]")
                    elif "type-parameter" in arg.type.type:
                        arg_repr.append("#")
                        self._identifier_map[arg.type.resolve_type()] = arg
                else:
                    arg_repr.append(arg.type.resolve_type())
            elif arg.kind == "Template":
                decl = arg.pointer()
                if (
                        decl.kind != "TemplateTemplateParmDecl"
                    ):
                    decl.set_ccm_identifier()
                    arg_repr.append(decl._ccm_identifier)
                else:
                    self._identifier_map[arg.pointer().id.name] = arg
                    arg_repr.append("#")
            elif arg.kind == "Null":
                arg_repr.append("null")
            elif arg.kind == "Declaration":
                arg_repr.append(
                        pointers.pointer_map[arg.pointer]._ccm_identifier
                        )
            elif arg.kind == "NullPtr":
                arg_repr.append("nullptr")
            elif arg.kind == "Integral":
                arg_repr.append(str(arg.integer))
            elif arg.kind == "TemplateExpansion":
                arg_repr.append("#")
            elif arg.kind == "Expression":
                arg_repr.append("(expr)")
            elif arg.kind == "Pack":
                if len(arg.parameter_pack):
                    arg_repr.append(
                            "{" +
                            f"{self.get_arglist_repr(arg.parameter_pack)}" +
                            "}"
                            )
                else:
                    arg_repr.append("[#...]")

        return ", ".join(arg_repr)


class CXXMethodDecl(FunctionDecl):

    def __init__(self):
        super().__init__()
        self.is_virtual = False
        self.is_static = False
        self.is_constexpr = False
        self.cxx_ctor_initializers = []
        self.overriden_methods = []
        return

    def load_content(self, obj: dict) -> dict:
        FunctionDecl.load_content(self, obj["function"])
        self.is_virtual = obj["is_virtual"]
        self.is_static = obj["is_static"]
        self.is_constexpr = obj["is_constexpr"]
        self.cxx_ctor_initializers = [
                CXXCtorInitializer.load_json(x, parent=self) for
                x in obj["cxx_ctor_initializers"]
                ]
        self.overriden_methods = [
                DeclRef.load_json(x, parent=self) for
                x in obj["overriden_methods"]
                ]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        FunctionDecl.set_ccm_identifier(self)
        if self.is_const or "const" in split_id(self.type):
            self.is_const = True
            self._local_ccm_identifier += " const"
            self._ccm_identifier += " const"
        return


class CXXConstructorDecl(CXXMethodDecl):

    def __init__(self):
        super().__init__()
        self.is_default = False
        self.is_copy_ctor = False
        self.is_move_ctor = False
        self.is_converting_ctor = False
        return

    def load_content(self, obj: dict) -> dict:
        CXXMethodDecl.load_content(self, obj["ctor"])
        self.is_default = obj["is_default"]
        self.is_copy_ctor = obj["is_copy_ctor"]
        self.is_move_ctor = obj["is_move_ctor"]
        self.is_converting_ctor = obj["is_converting_ctor"]
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        if self.name == "":
            self.name = self._parent.name
            self.qual_name[0] = self._parent.name
        FunctionDecl.set_ccm_identifier(self)
        ccm_id_parts = split_id(self._ccm_identifier)
        if (
                isinstance(self._parent, ClassTemplateDecl) or
                isinstance(self._parent, ClassTemplateSpecializationDecl)
        ):
            fname_end_idx = -2
            for rev_part_idx, part in enumerate(reversed(ccm_id_parts)):
                if part.startswith("<"):
                    fname_end_idx = -(rev_part_idx + 1)
                    break
                elif part.startswith("::"):
                    fname_end_idx = -rev_part_idx
                    break
            fname = ccm_id_parts[:fname_end_idx]
            arg_list = ccm_id_parts[-1]
            self._local_ccm_identifier = (
                    form_id([fname[-1], arg_list]).strip("::")
                    )
            ccm_id_parts = [*fname, arg_list]
        self._ccm_identifier = form_id(ccm_id_parts)
        return


class ClassTemplateDecl(CXXRecordDecl):

    def __init__(self):
        super().__init__()
        self.template_decl = None
        self.parameters = []
        self.specializations = []
        self.partial_specializations = []
        return

    def load_content(self, obj: dict) -> dict:
        self.template_decl = NamedDecl.load_json(obj["named_decl"])
        CXXRecordDecl.load_content(self, obj["cxx_record"])
        for xx in obj["parameters"]:
            if xx["param_type"] == "TemplateTypeParam":
                self.parameters.append(
                        TemplateTypeParmDecl.load_json(xx, parent=self)
                        )
            elif xx["param_type"] == "TemplateNonTypeParam":
                self.parameters.append(
                        TemplateNonTypeParmDecl.load_json(xx, parent=self)
                        )
            elif xx["param_type"] == "TemplateTemplateParam":
                self.parameters.append(
                        TemplateTemplateParmDecl.load_json(xx, parent=self)
                        )
            self.parameters[-1]._save = False
            self._named_decls.append(self.parameters[-1])
        self.specializations = [
                ClassTemplateSpecializationDecl.load_json(x, parent=self._parent) for
                x in obj["specializations"]
                ]
        for spec in self.specializations:
            spec._save = False
        self.partial_specializations = [
                ClassTemplatePartialSpecializationDecl.load_json(
                    x,
                    parent=self._parent
                    ) for
                x in obj["partial_specializations"]
                ]
        for pspec in self.partial_specializations:
            pspec._save = False
        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        NamedDecl.set_ccm_identifier(self)
        parm_reprs = []
        for parm in self.parameters:
            parm_reprs.append(parm.parm_repr())
        parm_list = "<" + ", ".join(parm_reprs) + ">"
        self._local_ccm_identifier += parm_list
        self._ccm_identifier += parm_list
        return


class FunctionTemplateDecl(FunctionDecl):

    def __init__(self):
        super().__init__()
        self.template_decl = None
        self.template_parameters = []
        self.specializations = []
        return

    def load_content(self, obj: dict) -> dict:
        self.template_decl = NamedDecl.load_json(obj["named_decl"])
        FunctionDecl.load_content(self, obj["function"])
        for xx in obj["parameters"]:
            if xx["param_type"] == "TemplateTypeParam":
                self.template_parameters.append(
                        TemplateTypeParmDecl.load_json(xx, parent=self)
                        )
            elif xx["param_type"] == "TemplateNonTypeParam":
                self.template_parameters.append(
                        TemplateNonTypeParmDecl.load_json(xx, parent=self)
                        )
            elif xx["param_type"] == "TemplateTemplateParam":
                self.template_parameters.append(
                        TemplateTemplateParmDecl.load_json(xx, parent=self)
                        )
            self.template_parameters[-1]._save = False
            self._named_decls.append(self.template_parameters[-1])
        self.specializations = [
                DeclFactory.create_variant(
                    JsonWrapper(x),
                    save=False,
                    parent=self) for
                x in obj["specializations"]
                ]
        for spec in [x for x in self.specializations if x is not None]:
            self._named_decls.append(spec)

        return obj

    def set_ccm_identifier(self) -> None:
        if self._ccm_identifier != "":
            return
        NamedDecl.set_ccm_identifier(self)
        parm_reprs = []
        for parm in self.template_parameters:
            parm_reprs.append(parm.parm_repr())
        parm_list = "<" + ", ".join(parm_reprs) + ">"

        self._local_ccm_identifier += parm_list
        self._local_ccm_identifier += self.get_arg_list()
      
        self._ccm_identifier += parm_list
        self._ccm_identifier += self.get_arg_list()
        return


class FriendDecl(Decl):

    def __init__(self):
        super().__init__()
        self.kind = None
        self.type = None
        self.friend = None
        return

    def load_content(self, obj: dict) -> dict:
        Decl.load_content(self, obj["decl"])
        self.kind = obj["kind"]
        self.type = obj["type"]
        self.friend = DeclFactory.create_variant(
                obj["friend"],
                save=False,
                parent=self
                )
        return


class TypeAliasDecl(TypeDecl):

    def __init__(self):
        super().__init__()
        self.underlying_type = None
        self.described_template = None
        return

    def load_content(self, obj: dict) -> dict:
        TypeDecl.load_content(self, obj["type_decl"])
        self.underlying_type = QualType.load_json(
                obj["underlying_type"],
                parent=self)
        self.described_template = (
                DeclPointer(obj["described_template"], self)
                )
        return obj


class TypeAliasTemplateDecl(TypeAliasDecl, IdContainer):

    def __init__(self):
        super().__init__()
        self.canonical_decl = -1
        self.template_parameters = []
        self.member_template = -1
        return

    def load_content(self, obj: dict) -> dict:
        TypeAliasDecl.load_content(self, obj["type_alias_decl"])
        self.canonical_decl = register_ptr(obj["canonical_decl"], self)
        for xx in obj["parameters"]:
            if xx["param_type"] == "TemplateTypeParam":
                self.template_parameters.append(
                        TemplateTypeParmDecl.load_json(
                            xx,
                            parent=self
                            )
                        )
            elif xx["param_type"] == "TemplateNonTypeParam":
                self.template_parameters.append(
                        TemplateNonTypeParmDecl.load_json(xx, parent=self)
                        )
            elif xx["param_type"] == "TemplateTemplateParam":
                self.template_parameters.append(
                        TemplateTemplateParmDecl.load_json(xx, parent=self)
                        )
            self.template_parameters[-1]._save = False
            self._named_decls.append(self.template_parameters[-1])
        self.member_template = DeclPointer(
                obj["member_template_decl"],
                self
                )
        return obj
    

class ClassTemplatePartialSpecializationDecl(ClassTemplateSpecializationDecl):

    def __init__(self):
        super().__init__()
        return

    def load_content(self, obj: dict) -> dict:
        ClassTemplateSpecializationDecl.load_content(
                self,
                obj["class_template_specialization"]
                )
        return obj


class ParmDecl(Name):

    def __init__(self):
        super().__init__()
        self.index = -1
        self.is_anonymous = False
        return

    def resolve_names(self) -> None:
        self.is_anonymous = self.name == ""
        param_prefix = (
                "f" if isinstance(self._parent, FunctionDecl) else
                "t"
                )
        self.name = (
                self.name if not self.is_anonymous
                else param_prefix + "param" + str(self.index)
                )
        self.qual_name = [self.name]
        self.qual_name.append(self._parent._ccm_identifier)
        return

    def set_ccm_identifier(self) -> None:
        self.resolve_names()
        NamedDecl.set_ccm_identifier(self)
        return


class TemplateTypeParmDecl(TypeDecl, ParmDecl):

    def __init__(self):
        super().__init__()
        self.param_type = ""
        self.template = -1
        self.with_typename = False
        self.depth = -1
        self.is_parameter_pack = False
        self.default = None
        return

    def load_content(self, obj: dict) -> dict:
        if SkippableVariant.load_content(self, obj):
            return
        TypeDecl.load_content(self, obj["type_decl"])
        self.template = DeclPointer(obj["template_decl"], self)
        self.param_type = obj["param_type"]
        self.with_typename = obj["with_typename"]
        self.index = obj["index"]
        self.depth = obj["depth"]
        self.is_parameter_pack = obj["is_parameter_pack"]
        self.default = QualType.load_json(
                obj["default"],
                parent=self
                )
        return obj

    def parm_repr(self) -> str:
        repres = ""
        if self.default:
            repres = "[" + self.default.type + "]"
        else:
            repres = "#"
        if self.is_parameter_pack:
            repres = "[" + repres + "...]"
        return repres

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return


class TemplateNonTypeParmDecl(ValueDecl, ParmDecl):

    def __init__(self):
        super().__init__()
        self.param_type = ""
        self.template = -1
        self.depth = -1
        self.is_parameter_pack = False
        self.type = None
        self.default = None
        return

    def load_content(self, obj: dict) -> dict:
        if SkippableVariant.load_content(self, obj):
            return
        ValueDecl.load_content(self, obj["value_decl"])
        self.param_type = obj["param_type"]
        self.template = DeclPointer(obj["template_decl"], self)
        self.index = obj["index"]
        self.depth = obj["depth"]
        self.is_parameter_pack = obj["is_parameter_pack"]
        self.type = QualType.load_json(obj["type"], parent=self)
        self.default = obj["default"]
        return obj

    def parm_repr(self) -> str:
        repres = f"{self.type.type}"
        if self.default:
            repres += f"[{self.default}]"
        else:
            repres += "#"
        if self.is_parameter_pack:
            repres = "[" + repres + "...]"
        return repres

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return


class TemplateTemplateParmDecl(NamedDecl, ParmDecl):

    def __init__(self):
        super().__init__()
        self.param_type = ""
        self.template = -1
        self.depth = -1
        self.is_parameter_pack = False
        self.default = None
        return

    def load_content(self, obj: dict) -> dict:
        if SkippableVariant.load_content(self, obj):
            return
        NamedDecl.load_content(self, obj["named_decl"])
        self.param_type = obj["param_type"]
        self.template = DeclPointer(obj["template_decl"], self)
        self.index = obj["index"]
        self.depth = obj["depth"]
        self.is_parameter_pack = obj["is_parameter_pack"]
        self.default = obj["default"]
        return obj

    def set_ccm_identifier(self) -> None:
        NamedDecl.set_ccm_identifier(self)
        return

    def parm_repr(self) -> str:
        repres = ""
        if self.default:
            repres = "[" + self.default + "]"
        else:
            repres = "#"
        if self.is_parameter_pack:
            repres = "[" + "#" + "...]"
        return repres


class ParmVarDecl(ValueDecl, ParmDecl):

    def __init__(self):
        super().__init__()
        self.has_default = False
        self.default_value = None
        return

    def load_content(self, obj: dict) -> dict:
        ValueDecl.load_content(self, obj["value_decl"])
        self.has_default = obj["has_default"]
        self.default_value = obj["default_value"]
        self.index = obj["index"]
        return obj

    def set_ccm_identifier(self) -> None:
        ParmDecl.set_ccm_identifier(self)
        return
    

class DeclFactory(object):

    def create_variant(
            obj: dict,
            save: bool = True,
            parent: Optional["Variant"] = None) -> "Decl":

        if obj is None:
            return None

        out = None
        variant = obj["kind"]
        content = obj["content"]

        if content is None and obj["skipped"]:
            out = SkippableVariant.load_json(obj)
        elif content["skipped"]:
            out = SkippableVariant.load_json(content)
        elif variant == "CapturedDecl":
            out = CapturedDecl.load_json(content)
        elif variant == "LinkageSpecDecl":
            out = LinkageSpecDecl.load_json(content)
        elif variant == "NamespaceDecl":
            out = NamespaceDecl.load_json(content)
        elif variant == "TypeDecl":
            out = TypeDecl.load_json(content)
        elif variant == "TagDecl":
            out = TagDecl.load_json(content)
        elif variant == "ValueDecl":
            out = ValueDecl.load_json(content)
        elif variant == "TranslationUnitDecl":
            out = TranslationUnitDecl.load_json(content)
        elif variant == "TypedefDecl":
            out = TypedefDecl.load_json(content)
        elif variant == "EnumDecl":
            out = EnumDecl.load_json(content)
        elif variant == "RecordDecl":
            out = RecordDecl.load_json(content)
        elif variant == "EnumConstantDecl":
            out = EnumConstantDecl.load_json(content)
        elif variant == "IndirectFieldDecl":
            out = IndirectFieldDecl.load_json(content)
        elif variant == "FunctionDecl":
            out = FunctionDecl.load_json(content)
        elif variant == "FieldDecl":
            out = FieldDecl.load_json(content)
        elif variant == "VarDecl":
            out = VarDecl.load_json(content)
        elif variant == "UsingDirectiveDecl":
            out = UsingDirectiveDecl.load_json(content)
        elif variant == "NamespaceAliasDecl":
            out = NamespaceAliasDecl.load_json(content)
        elif variant == "CXXRecordDecl":
            out = CXXRecordDecl.load_json(content)
        elif variant == "ClassTemplateSpecializationDecl":
            out = ClassTemplateSpecializationDecl.load_json(content)
        elif variant == "CXXConstructorDecl":
            out = CXXConstructorDecl.load_json(content)
        elif variant == "ClassTemplateDecl":
            out = ClassTemplateDecl.load_json(content)
        elif variant == "FunctionTemplateDecl":
            out = FunctionTemplateDecl.load_json(content)
        elif variant == "FriendDecl":
            out = FriendDecl.load_json(content)
        elif variant == "TypeAliasDecl":
            out = TypeAliasDecl.load_json(content)
        elif variant == "TypeAliasTemplateDecl":
            out = TypeAliasTemplateDecl.load_json(content)
        elif variant == "ClassTemplatePartialSpecializationDecl":
            out = ClassTemplatePartialSpecializationDecl.load_json(content)
        elif variant == "TemplateTypeParmDecl":
            out = TemplateTypeParmDecl.load_json(content)
        elif variant == "NonTypeTemplateParmDecl":
            out = TemplateNonTypeParmDecl.load_json(content)
        elif variant == "TemplateTemplateParmDecl":
            out = TemplateTemplateParmDecl.load_json(content)
        elif variant == "ParmVarDecl":
            out = ParmVarDecl.load_json(content)
        elif variant == "CXXMethodDecl":
            out = CXXMethodDecl.load_json(content)
        else:
            return None
            
        out.clang_kind = obj["clang_kind"]
        out.kind = variant
        out._save = save
        out._json = obj
        out._parent = parent

        return out


################################# stmts #######################################


class StmtFactory(object):

    def create_variant(
            obj: dict,
            save: bool = True,
            parent: Optional["Variant"] = None) -> "Stmt":
        if obj is None:
            return None

        out = None
        variant = obj["kind"]
        content = obj["content"]

        if content is None and obj["skipped"]:
            out = SkippableVariant.load_json(obj)
        elif content["skipped"]:
            out = SkippableVariant.load_json(content)
        elif variant == "Stmt":
            out = Stmt.load_json(content, parent=self)
        elif variant == "DeclStmt":
            out = DeclStmt.load_json(content, parent=self)
        else:
            return ExprFactory.create_variant(obj, save, parent=parent)

        out.clang_kind = obj["clang_kind"]
        out.kind = variant
        out._save = save
        out._json = obj
        out._parent = parent

        return out


################################# exprs #######################################


class Expr(Stmt):

    def __init__(self):
        super().__init__()
        self.qual_type = None
        self.value_kind = None
        self.object_kind = None
        return

    def load_content(self, obj: dict) -> dict:
        content = Stmt.load_content(self, obj)
        content = content["expr"]
        self.qual_type = QualType.load_json(content["qual_type"], parent=self)
        self.value_kind = content["value_kind"]
        self.object_kind = content["object_kind"]
        return content


class CXXBaseSpecifier(Variant):

    def __init__(self):
        super().__init__()
        self.name = ""
        self.template = None
        self.virtual = False
        return

    def load_content(self, obj: dict) -> dict:
        self.name = obj["name"]
        self.template = obj["template"]
        self.virtual = obj["virtual"]
        return obj


class DeclRefExpr(Expr):

    def __init__(self):
        super().__init__()
        self.decl_ref = None
        self.found_decl_ref = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.decl_ref = DeclRef.load_json(obj["decl_ref"], parent=self)
        self.found_decl_ref = DeclRef.load_json(obj["decl_ref"], parent=self)
        return obj


class OverloadExpr(Expr):

    def __init__(self):
        super().__init__()
        self.decls = []
        self.name = ""
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.decls = [
                DeclRef.load_json(x, parent=self) for x in obj["decls"]
                ]
        self.name = obj["name"]
        return obj


class CharacterLiteral(Expr):

    def __init__(self):
        super().__init__()
        self.value = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.value = obj["value"]
        return obj


class IntegerLiteral(Expr):

    def __init__(self):
        super().__init__()
        self.is_signed = False
        self.bitwidth = -1
        self.value = ""
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.is_signed = obj["value"]["is_signed"]
        self.bitwidth = obj["value"]["bitwidth"]
        self.value = obj["value"]["value"]
        return obj


class FixedPointLiteral(Expr):

    def __init__(self):
        super().__init__()
        self.value = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.value = obj["value"]
        return obj


class FloatingPointLiteral(Expr):

    def __init__(self):
        super().__init__()
        self.value = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.value = obj["value"]
        return obj


class StringLiteral(Expr):

    def __init__(self):
        super().__init__()
        self.value = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.value = obj["value"]
        return obj


class MemberExpr(Expr):

    def __init__(self):
        super().__init__()
        self.is_arrow = False
        self.performs_virtual_dispatch = False
        self.id = None
        self.decl_ref = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.is_arrow = obj["is_arrow"]
        self.performs_virtual_dispatch = obj["performs_virtual_dispatch"]
        self.id = Name.load_json(obj["id"])
        self.decl_ref = DeclRef.load_json(obj["decl_ref"], parent=self)
        return obj


class CXXDefaultArgExpr(Expr):

    def __init__(self):
        super().__init__()
        self.init_expr = None
        return

    def load_content(self, obj: dict) -> dict:
        Expr.load_content(self, obj["expr"])
        self.init_expr = StmtFactory.create_variant(
                obj["init_expr"],
                save=False,
                parent=self
                )
        if self.init_expr is not None:
            self.init_expr.parent(self)

        return obj


class CXXDefaultInitExpr(CXXDefaultArgExpr):

    def __init__(self):
        super().__init__()
        return


class ExprFactory(object):

    def create_variant(
            obj: dict,
            save: bool = True,
            parent: Optional["Variant"] = None) -> "Expr":
        if obj is None:
            return None

        out = None
        variant = obj["kind"]
        content = obj["content"]

        if content is None and obj["skipped"]:
            out = SkippableVariant.load_json(obj)
        elif content["skipped"]:
            out = SkippableVariant.load_json(content)
        elif variant == "CXXBaseSpecifier":
            out = CXXBaseSpecifier.load_json(content)
        elif variant == "DeclRefExpr":
            out = DeclRefExpr.load_json(content)
        elif variant == "OverloadExpr":
            out = OverloadExpr.load_json(content)
        elif variant == "CharacterLiteral":
            out = CharacterLiteral.load_json(content)
        elif variant == "IntegerLiteral":
            out = IntegerLiteral.load_json(content)
        elif variant == "FloatingPointLiteral":
            out = FloatingPointLiteral.load_json(content)
        elif variant == "FixedPointLiteral":
            out = FixedPointLiteral.load_json(content)
        elif variant == "StringLiteral":
            out = StringLiteral.load_json(content)
        elif variant == "MemberExpr":
            out = MemberExpr.load_json(content)
        elif variant == "CXXDefaultArgExpr":
            out = CXXDefaultArgExpr.load_json(content)
        elif variant == "CXXDefaultInitExpr":
            out = CXXDefaultInitExpr.load_json(content)
        else:
            return None

        out.clang_kind = obj["clang_kind"]
        out.kind = variant
        out._save = save
        out._json = obj

        return out

from decls import (
    TemplateInstantiationArgInfo
    QualType
)
from .factories import Type

class AdjustedType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "AdjustedType":
        return AdjustedType.load_json_type_with_child(objs)


class ArrayType(Type):

    def __init__(self):
        Type.__init__(self)
        self.element_type = None
        self.stride = None

        return

    @staticmethod
    def load_json(objs: list) -> "ArrayType":
        out = ArrayType.load_json_type(objs)
        out.element_type = objs[2]["element_type"]
        out.stride = None if "stride" not in objs[2] else objs[2]["stride"]
        return out


class ConstantArrayType(ArrayType):

    def __init__(self):
        ArrayType.__init__(self)
        self.length = -1
        return

    @staticmethod
    def load_json(objs: list) -> "ConstantArrayType":
        out = ConstantArrayType.load_json(objs)
        out.length = objs[2]
        return out


class VariableArrayType(ArrayType):

    def __init__(self):
        ArrayType.__init__(self)
        self.length_expr = None
        return

    @staticmethod
    def load_json(objs: list) -> "VariableArrayType":
        out = VariableArrayType.load_json(objs)
        out.length_expr = objs[2]
        return out


class AtomicType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "AtomicTypeTuple":
        return AtomicTypeTuple.load_json_type_with_child(objs)


class AttributedType(Type):

    def __init__(self):
        Type.__init__(self)
        self.attr_kind = ""
        self.lifetime = None
        return

    @staticmethod
    def load_json(objs: list) -> "AttributedType":
        out = Type.load_json_type(objs)
        out.attr_kind = objs[2]["attr_kind"]
        out.lifetime = None if "lifetime" not in objs[2] else objs[2]["lifetime"]
        return out


class BlockPointerType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "BlockPointerType":
        return BlockPointerType.load_json_type_with_child(objs)


class BuiltinType(Type):

    def __init__(self):
        Type.__init__(self)
        self.builtin_type = ""
        return

    @staticmethod
    def load_json(objs: list) -> "BuiltinType":
        out = BuiltinType.load_json_type(objs)
        out.builtin_type = objs[2]
        return out


class DecltypeType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "DecltypeType":
        return DecltypeType.load_json_type_with_child(objs)


class FunctionType(Type):

    def __init__(self):
        Type.__init__(self)
        self.return_type = None
        return

    @staticmethod
    def load_json(objs) -> "FunctionType":
        out = FunctionType.load_json_type(objs)
        out.return_type = QualType.load_json(objs[2])
        return out


class FunctionProtoType(FunctionType):

    def __init__(self):
        FunctionType.__init__(self)
        self.param_types = []
        return

    @staticmethod
    def load_json(objs: list) -> "FunctionProtoType":
        out = FunctionProtoType.load_json(objs)
        for p in objs[2]["params_type"]:
            out.append(QualType.load_json(p))
        return out


class MemberPointerType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "MemberPointerType":
        return MemberPointerType.load_json_type_with_child(objs)


class ParenType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "ParenType":
        return ParenType.load_json_type_with_child(objs)


class PointerType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "PointerType":
        return PointerType.load_json_type_with_child(objs)


class ReferenceType(Type):

    def __init__(self):
        Type.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "ReferenceType":
        return ReferenceType.load_json_type_with_child(objs)


class TagType(Type):

    def __init__(self):
        Type.__init__(self)
        self.pointer = -1
        return

    @staticmethod
    def load_json(objs: list) -> "TagType":
        out = TagType.load_json_type(objs)
        out.pointer = objs[2]
        return out


class TypedefType(Type):

    def __init__(self):
        Type.__init__(self)
        self.child_type = None
        self.decl_pointer = -1
        return

    @staticmethod
    def load_json(objs: list) -> "TypedefType":
        out = TypedefType.load_json_type(objs)
        out.child_type = objs[2]["child_type"]
        out.decl_pointer = objs[2]["decl_ptr"]
        return out


class TemplateTypeParmType(Type):

    def __init__(self):
        Type.__init__(self)
        self.id = ""
        self.depth = -1
        self.index = -1
        self.variadic = False
        self.parameter = -1
        self.desugared_type = None
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateTypeParmType":
        out = TemplateTypeParmType.load_json_type(objs)
        out.id = objs[2]["id"]
        out.depth = objs[2]["depth"]
        out.index = objs[2]["index"]
        out.variadic = objs[2]["is_pack"]
        out.parameter = objs[2]["parm"]
        out.desugared_type = None if "desugared_type" not in objs[2] else objs[2]["desugared_type"]
        return out


class SubstTemplateTypeParmType(Type):

    def __init__(self):
        Type.__init__(self)
        self.replaced = -1
        self.replacement_type = None
        self.desugared_type = None
        return

    @staticmethod
    def load_json(objs: list) -> "SubstTemplateTypeParmType":
        out = SubstTemplateTypeParmType.load_json_type(objs)
        out.replaced = objs[2]["replaced"]
        out.replacement_type = QualType.load_json(objs[2]["replacement_type"])
        out.desugared_type = None if "desugared_type" not in objs[2] else objs[2]["desugared_type"]
        return out


class TemplateSpecializationType(Type):

    def __init__(self):
        Type.__init__(self)
        self.type_alias = False
        self.template_decl = -1
        self.aliased_type = None
        self.desugared_type = None
        self.specialization_args = []
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateSpecializationType":
        out = TemplateSpecializationType.load_json_type(objs)
        out.type_alias = objs[2]["type_alias"]
        out.template_decl = objs[2]["template_decl"]
        out.aliased_type = None if "aliased_type" not in objs[2] else objs[2]["aliased_type"]
        out.desugared_type = None if "desugared_type" not in objs[2] else objs[2]["desugared_type"]
        for sa in objs[2]["specialization_args"]:
            out.append(TemplateInstantiationArgInfo.load_json(sa))
        return out


class InjectedClassType(Type):

    def __init__(self):
        Type.__init__(self)
        self.injected_specialization_type = None
        self.desugared_type = None
        return

    @staticmethod
    def load_json(objs: list) -> "InjectedClassType":
        out = InjectedClassType.load_json_type(objs)
        out.injected_specialization_type = QualType.load_json(objs[2]["injected_specialization_type"])
        out.desugared_type = None if "desugared_type" not in objs[2] else objs[2]["desugared_type"]
        return out


class DependentNameType(Type):

    def __init__(self):
        Type.__init__(self)
        self.identifier = ""
        self.desugared_type = None
        return

    @staticmethod
    def load_json(objs: list) -> "DependentNameType":
        out = DependentNameType.load_json_type(objs)
        out.identifier = objs[2]["identifier"]
        out.desugared_type = None if "desugared_type" not in objs[2] else objs[2]["desugared_type"]
        return out


type_ptr_map = {}
integer_type_widths = {
        "char_type": -1,
        "short_type": -1,
        "int_type": -1,
        "long_type": -1,
        "longlong_type": -1
}


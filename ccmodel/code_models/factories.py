from .types import *
from .decls import *
from .stmt import *
from .expr import *


class TypeFactory(object):

    @staticmethod
    def create_variant(objs: list) -> "Type":

        out = None
        variant = objs[0]
        if variant == "AdjustedType":
            out = AdjustedType.load_json(objs)
        if variant == "ArrayType":
            out = ArrayType.load_json(objs)
        if variant == "ConstantArrayType":
            out = ConstantArrayType.load_json(objs)
        if variant == "VariableArrayType":
            out = VariableArrayType.load_json(objs)
        if variant == "AtomicType":
            out = AtomicType.load_json(objs)
        if variant == "AttributedType":
            out = AttributedType.load_json(objs)
        if variant == "BlockPointerType":
            out = BlockPointerType.load_json(objs)
        if variant == "BuiltinType":
            out = BuiltinType.load_json(objs)
        if variant == "DecltypeType":
            out = DecltypeType.load_json(objs)
        if variant == "FunctionType":
            out = FunctionType.load_json(objs)
        if variant == "FunctionProtoType":
            out = FunctionProtoType.load_json(objs)
        if variant == "MemberPointerType":
            out = MemberPointerType.load_json(objs)
        if variant == "PointerType":
            out = PointerType.load_json(objs)
        if variant == "ReferenceType":
            out = ReferenceType.load_json(objs)
        if variant == "TagType":
            out = TagType.load_json(objs)
        if variant == "TypedefType":
            out = TypedefType.load_json(objs)
        if variant == "TemplateTypeParmType":
            out = TemplateTypeParmType.load_json(objs)
        if variant == "SubstTemplateTypeParmType":
            out = SubstTemplateTypeParmType.load_json(objs)
        if variant == "TemplateSpecializationType":
            out = TemplateSpecializationType.load_json(objs)
        if variant == "InjectedClassType":
            out = InjectedClassType.load_json(objs)
        if variant == "DependentNameType":
            out = DependentNameType.load_json(objs)
        else:
            out = Type.load_json_type(objs)

        return out

class DeclFactory(Object):

    @staticmethod
    def create_variant(objs: list) -> "Decl":

        out = None
        variant = objs[0]
        if variant == "CapturedDecl":
                out = CapturedDecl.load_json(objs)
        elif variant == "LinkageSpecDecl":
            out = LinkageSpecDecl.load_json(objs)
        elif variant == "NamespaceDecl":
            out = NamespaceDecl.load_json(objs)
        elif variant == "TypeDecl":
            out = TypeDecl.load_json(objs)
        elif variant == "TagDecl":
            out = TagDecl.load_json(objs)
        elif variant == "ValueDecl":
            out = ValueDecl.load_json(objs)
        elif variant == "TranslationUnitDecl":
            out = TranslationUnitDecl.load_json(objs)
        elif variant == "TypedefNameDecl":
            out = TypedefNameDecl.load_json(objs)
        elif variant == "TypedefDecl":
            out = TypedefDecl.load_json(objs)
        elif variant == "EnumDecl":
            out = EnumDecl.load_json(objs)
        elif variant == "RecordDecl":
            out = RecordDecl.load_json(objs)
        elif variant == "EnumConstantDecl":
            out = EnumConstantDecl.load_json(objs)
        elif variant == "IndirectFieldDecl":
            out = IndirectFieldDecl.load_json(objs)
        elif variant == "DeclaratorDecl":
            out = DeclaratorDecl.load_json(objs)
        elif variant == "FunctionDecl":
            out = FunctionDecl.load_json(objs)
        elif variant == "FieldDecl":
            out = FieldDecl.load_json(objs)
        elif variant == "VarDecl":
            out = VarDecl.load_json(objs)
        elif variant == "UsingDirectiveDecl":
            out = UsingDirectiveDecl.load_json(objs)
        elif variant == "NamespaceAliasDecl":
            out = NamespaceAliasDecl.load_json(objs)
        elif variant == "CXXRecordDecl":
            out = CXXRecordDecl.load_json(objs)
        elif variant == "ClassTemplateSpecializationDecl":
            out = ClassTemplateSpecializationObject.load_json(objs)
        elif variant == "CXXConstructorDecl":
            out = CXXConstructorDecl.load_json(objs)
        elif variant == "TemplateDecl":
            out = TemplateDecl.load_json(objs)
        elif variant == "RedeclarableTemplateDecl":
            out = RedeclarableTemplateDecl.load_json(objs)
        elif variant == "ClassTemplateDecl":
            out = ClassTemplateDecl.load_json(objs)
        elif variant == "FunctionTemplateDecl":
            out = FunctionTemplateDecl.load_json(objs)
        elif variant == "FriendDecl":
            out = FriendDecl.load_json(objs)
        elif variant == "TypeAliasDecl":
            out = TypeAliasDecl.load_json(objs)
        elif variant == "TypeAliasTemplateDecl":
            out = TypeAliasTemplateDecl.load_json(objs)
        elif variant == "ClassTemplatePartialSpecializationDecl":
            out = ClassTemplatePartialSpecializationDecl(objs)
        elif variant == "TemplateTypeParmDecl":
            out = TemplateTypeParmDecl.load_json(objs)
        elif variant == "NonTypeTemplateParmDecl":
            out = NonTypeTemplateParmDecl.load_json(objs)
        elif variant == "TemplateTemplateParmDecl":
            out = TemplateTemplateParmDecl(objs)
        elif variant == "BlockDecl":
            out = BlockDecl.load_json(objs)

        return out

class StmtFactory(object):

    @staticmethod
    def create_variant(objs: list) -> "Stmt":
       
        out = None
        variant = objs[0]

        if variant == "Stmt":
            out = Stmt.load_json(objs)
        elif variant == "DeclStmt":
            out = DeclStmt.load_json(objs)
        elif variant == "IfStmt":
            out = IfStmt.load_json(objs)
        elif variant == "SwitchStmt":
            out = SwitchStmt.load_json(objs)
        elif variant == "AttributedStmt":
            out = AttributedStmt.load_json(objs)
        elif variant == "LabelStmt":
            out = LabelStmt.load_json(objs)
        elif variant == "GotoStmt":
            out = GotoStmt.load_json(objs)
        elif variant == "CXXCatchStmt":
            out = CXXCatchStmt.load_json(objs)

        return out


class ExprFactory(object):


    @staticmethod
    def create_variant(objs: list) -> "Expr":
        pass



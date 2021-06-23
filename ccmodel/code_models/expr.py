from .basic import (
        SourceRange,
        DeclRef,
        Decl,
        NamedDecl,
        Stmt,
        Expr,
        QualType
)


class CXXBaseSpecifier(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.name = ""
        self.template = None
        self.virtual = False
        return

    def load_data(self, objs) -> None:
        Expr.load_data(self, objs[1])
        self.name = objs[2]["name"]

        self.template = (
                None if "template" not in objs[2] else
                objs[2]["template"]
        )
        self.virtual = (
                False if "virtual" not in objs[2] else
                objs[2]["virtual"]
        )
        return


class CastExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.cast_kind = ""
        self.base_path = []
        return

    def load_data(self, objs) -> None:
        Expr.load_data(self, objs[1])
        self.cast_kind = objs[2]["cast_kind"]
        for b in objs[2]["base_path"]:
            self.base_path.append(CXXBaseSpecifier.load_json(b))
        return


class ExplicitCastExpr(CastExpr):

    def __init__(self):
        CastExpr.__init__(self)
        self.type = None
        return

    def load_data(self, objs: list) -> None:
        CastExpr.load_data(objs[1])
        self.type = QualType.load_json(objs[2])
        return


class DeclRefExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.decl_ref = None
        self.found_decl_ref = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(objs[1])
        self.decl_ref = (
                None if "decl_ref" not in objs[2] else
                objs[2]["decl_ref"]
                )
        self.found_decl_ref = (
                None if "found_decl_ref" not in objs[2] else
                objs[2]["found_decl_ref"]
                )
        return


class OverloadExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.decls = []
        self.name = ""
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        data = objs[2]
        if "decls" in objs[2]:
            for d in objs[2]["decls"]:
                self.decls.append(DeclRef(d))
        self.name = objs[2]["name"]
        return


class UnresolvedLookupExpr(OverloadExpr):

    def __init__(self):
        OverloadExpr.__init__(self)
        self.requires_adl = False
        self.is_overloaded = False
        self.naming_class = None
        return

    def load_data(self, objs: list) -> None:
        OverloadExpr.load_data(self, objs[1])

        if "requires_ADL" in objs[2]:
            self.requires_adl = objs[2]["requires_adl"]
        if "is_overloaded" in objs[2]:
            self.is_overloaded = objs[2]["is_overloaded"]
        if "naming_class" in objs[2]:
            self.naming_class = DeclRef.load_json(objs[2]["naming_class"])

        return


class PredefinedExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.type = ""
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(objs[1])
        self.type = objs[2]
        return


class CharacterLiteral(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.value = objs[2]
        return


class IntegerLiteral(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.is_signed = False
        self.bitwidth = -1
        self.value = ""
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        
        if "is_signed" in objs[2]:
            self.is_signed = objs[2]["is_signed"]
        self.bitwidth = objs[2]["bitwidth"]
        self.value = objs[2]["value"]
        return


class FixedPointLiteral(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.value = objs[2]
        return


class FloatingPointLiteral(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.value = objs[2]
        return


class StringLiteral(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.value = "".join(objs[2])
        return


class OffsetOfExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.literal = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        if "literal" in objs[2]:
            self.literal = IntegerLiteral.load_json(objs[2]["literal"])
        return


class UnaryOperator(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.kind = ""
        self.is_postfix = False
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.kind = objs[2]["kind"]
        self.is_postfix = (
                False if "is_postfix" not in objs[2]
                else objs[2]["is_postfix"]
                )
        return


class UnaryExprOrTypeTraitExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.kind = ""
        self.qual_type = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.kind = objs[2]["kind"]
        self.qual_type = QualType.load_json(
                objs[2]["qual_type"]
                )
        return


class MemberExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.is_arrow = False
        self.performs_virtual_dispatch = False
        self.name = None
        self.decl_ref = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        data = objs[2]
        self.is_arrow = (
                False if "is_arrow" not in data
                else data["is_arrow"]
                )
        self.performs_virtual_dispatch = (
                False if "performs_virtual_dispatch" not in data
                else data["performs_virtual_dispatch"]
                )
        self.name = NamedDecl.load_json(data["name"])
        self.decl_ref = DeclRef.load_json(data["decl_ref"])
        return


class ExtVectorElementExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.name = ""
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.name = objs[2]
        return


class BinaryOperator(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.kind = ""
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.kind = objs[2]["kind"]
        return


class CompoundAssignOperator(BinaryOperator):

    def __init__(self):
        BinaryOperator.__init__(self)
        self.lhs_type = None
        self.result_type = None
        return

    def load_data(self, objs: list) -> None:
        BinaryOperator.load_data(self, objs[1])

        data = objs[2]
        self.lhs_type = QualType.load_json(data["lhs_type"])
        self.result_type = QualType.load_json(data["result_type"])
        return


class BlockExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.block_decl = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.block_decl = Decl.load_json(objs[2])
        return


class OpaqueValueExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.source_expr = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.source_expr = (
                None if "source_expr" not in objs[2]
                else Stmt.load_json(objs["source_expr"])
                )
        return


class AddrLabelExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.label = ""
        self.pointer = -1
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.label = objs[2]["label"]
        self.pointer = objs[2]["pointer"]

        return


class CXXNamedCastExpr(ExplicitCastExpr):

    def __init__(self):
        ExplicitCastExpr.__init__(self)
        self.cast_name = ""
        return

    def load_data(self, objs: list) -> None:
        ExplicitCastExpr.load_data(self, objs[1])
        self.cast_name = objs[2]
        return


class CXXBoolLiteralExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = -1
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.value = objs[2]
        return


class CXXConstructExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.decl_ref = None
        self.is_elidable = False
        self.requires_zero_initialization = False
        self.is_copy_constructor = False
        return


    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        data = objs[2]
        self.decl_ref = DeclRef.load_json(data["decl_ref"])
        self.is_elidable = (
                False if "is_elidable" not in data
                else data["is_elidable"]
                )
        self.requires_zero_initialization = (
                False if "requires_zero_initialization" not in data
                else data["requires_zero_initialization"]
                )
        self.is_copy_constructor = (
                False if "is_copy_constructor" not in data
                else data["is_copy_constructor"]
                )
        return


CXXInheritedCtorInitExpr = CXXConstructExpr


class CXXBindTemporaryExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.cxx_temporary = -1
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.cxx_temporary = objs[2]["cxx_temporary"]
        return


class MaterializeTemporaryExpr(Expr):
    
    def __init__(self):
        Expr.__init__(self)
        self.decl_ref = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.decl_ref = (
                None if "decl_ref" not in objs[2]
                else DeclRef.load_json(objs[2]["decl_ref"])
                )
        return

class ExprWithCleanups(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.decl_refs = []
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.decl_refs = (
                [] if "decl_refs" not in objs[2]
                else [DeclRef.load_json(x) for x in objs[2]["decl_refs"])
        return



class LambdaExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.lambda_decl = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        self.lambda_decl = Decl.load_json(objs[2])
        return


class CXXNewExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.is_array = False
        self.array_size_expr = None
        self.initializer_expr = None
        self.placement_args = []
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])
        
        data = objs[2]
        self.is_array = (
                False if "is_array" not in data
                else data["is_array"]
                )
        self.array_size_expr = (
                None if "array_size_expr" not in data
                else data["array_size_expr"]
                )
        self.initializer_expr = (
                None if "initializer_expr" not in data
                else data["initializer_expr"]
                )
        self.placement_args = (
                [] if "placement_args" not in data
                else data["placement_args"]
                )
        return


class CXXDeleteExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.is_array = False
        self.destroyed_type = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.is_array = (
                False if "is_array" not in objs[2]
                else objs[2]["is_array"]
                )
        self.destroyed_type = QualType.load_json(
                objs[2]["destroyed_type"]
                )
        return


class CXXDefaultArgExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.init_expr = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.init_expr = (
                None if "init_expr" not in objs[2]
                else Stmt.load_json(objs[2]["init_expr"])
                )
        return


class CXXDefaultInitExpr(CXXDefaultArgExpr):

    def __init__(self):
        CXXDefaultArgExpr.__init__(self)
        return


class TypeTraitExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = False
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.value = (
                False if "value" not in objs[2]
                else objs[2]["value"]
                )
        return


class GenericSelectionExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.value = (
                None if "value" not in objs[2]
                else Stmt.load_json(objs[2]["value"])
                )
        return


class CXXNoexceptExpr(Expr):

    def __init__(self):
        Expr.__init__(self)
        self.value = None
        return

    def load_data(self, objs: list) -> None:
        Expr.load_data(self, objs[1])

        self.value = (
                None if "value" not in objs[2]
                else objs[2]["value"]
                )
        return








from .basic import (
        QualType,
        DeclRef,
        Decl,
        NamedDecl,
        BlockCapturedVariable,
        CXXCtorInitializer,
        TemplateSpecialization,
        TemplateArgument,
        TemplateInstantiationArgInfo,
        TemplateSpecializationInfo,
        NestedNameSpecifierLoc,
        BaseInfo,
        LambdaCaptureInfo,
        SourceRange
)


class DeclContext(Object):

    def __init__(self):
        self.decls = []
        self.c_linkage = False
        self.has_external_lexical_storage = None
        self.has_external_visible_storage = None
        return

    @staticmethod
    def load_json(objs: list) -> "Decl":
        out = DeclContext()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        self.decls = objs[1]
        self.c_linkage = objs[2]["c_linkage"]
        self.has_external_lexical_storage = (
            None if "has_external_lexical_storage" not in objs[2]
            else objs[2]["has_external_lexical_storage"]
        )
        self.has_external_visible_storage = (
            None if "has_external_visible_storage" not in objs[2]
            else objs[2]["has_external_visible_storage"]
        )
        return


class CapturedDecl(Decl, DeclContext):

    def __init__(self):
        Decl.__init__(self)
        DeclContext.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "CapturedDecl":
        out = CapturedDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        Decl.load_data(self, objs[0])
        DeclContext.load_data(self, objs[1])
        return


class LinkageSpecDecl(Decl, DeclContext):

    def __init__(self):
        Decl.__init__(self)
        DeclContext.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "LinkageSpecDecl":
        out = LinkageSpecDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        Decl.load_data(self, objs[1])
        DeclContext.load_data(out, objs[2])
        return


class NamespaceDecl(NamedDecl, DeclContext):

    def __init__(self):
        NamedDecl.__init__(self)
        DeclContext.__init__(self)
        self.is_inline = False
        self.original_namespace = None
        return

    @staticmethod
    def load_json(objs: list) -> "NamespaceDecl":
        out = NamespaceDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamedDecl.load_data(self, objs[1])
        DeclContext.load_data(self, objs[2])
        self.is_inline = objs[3]["is_inline"]
        self.original_namespace = (
                None if "original_namespace" not in objs[3] else
                objs[3]["original_namespace"]
        )
        return


class TypeDecl(NamedDecl):

    def __init__(self):
        NamedDecl.__init__(self)
        self.type_ptr = -1
        return

    @staticmethod
    def load_json(objs: list) -> "TypeDecl":
        out = TypeDecl()
        out.load_data(objs)
        return out

    def load_data(self, obj: list) -> None:
        NamedDecl.load_data(self, objs[0])
        self.type_ptr = objs[1]
        return


class TagDecl(TypeDecl, DeclContext):

    def __init__(self):
        TypeDecl.__init__(self)
        DeclContext.__init__(self)
        self.tag_kind = ""
        return

    @staticmethod
    def load_json(objs: list) -> "TagDecl":
        out = TagDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TypeDecl.load_data(self, objs[1])
        DeclContext.load_data(self, objs[2])
        self.tag_kind = objs[3]
        return


class ValueDecl(NamedDecl, QualType):

    def __init__(self):
        NamedDecl.__init__(self)
        QualType.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "ValueDecl":
        out = ValueDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamedDecl.load_data(self, objs[1])
        QualType.load_data(self, objs[2])
        return


class TranslationUnitDecl(Object):
    
    def __init__(self):
        self.input_kind = ""
        return

    @staticmethod
    def load_json(obj: str) -> "TranslationUnitDecl":
        out = TranslationUnitDecl()
        out.input_kind = obj
        return out


class TypdefNameDecl(TypeDecl):

    def __init__(self):
        TypeDecl.__init__(self)
        self.underlying_type = None
        self.is_module_private = False
        return

    @staticmethod
    def load_json(objs: list) -> "TypedefNameDecl":
        out = TypedefNameDecl()
        out.load_data(objs)
        return out

    def load_data(objs: list) -> None:
        TypeDecl.load_data(objs[1])
        return

class TypedefDecl(TypedefNameDecl):

    def __init__(self):
        TypedefNameDecl.__init__(self)
        self.underlying_type = None
        self.is_module_private = False

    @staticmethod
    def load_json(objs: list) -> "TypedefDecl":
        out = TypedefDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TypedefNameDecl.load_data(self, objs[1])
        self.underlying_type = QualType.load_json(objs[2]["qual_type"])
        self.is_module_private = (
                False if "is_module_private" not in objs[2]
                else obj[2]["is_module_private"]
        )
        return


class EnumDecl(TagDecl):

    def __init__(self):
        TagDecl.__init__(self)
        self.scope = ""
        self.is_module_private = False
        return

    @staticmethod
    def load_json(objs: list) -> "EnumDecl":
        out = EnumDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TagDecl.load_data(self, objs[1])
        self.scope = "" if "scope" not in objs[2] else objs[2]["scope"]
        self.is_module_private = (
                False if "is_module_private" not in objs[2]
                else objs[2]["is_module_private"]
        )
        return


class RecordDecl(TagDecl):

    def __init__(self):
        TagDecl.__init__(self)
        self.definition_ptr = -1
        self.is_module_private = False
        self.is_complete_definition = False
        self.is_dependent_type = False
        return

    @staticmethod
    def load_json(objs: list) -> "RecordDecl":
        out = RecordDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TagDecl.load_data(objs[1])
        self.definition_ptr = objs[2]["definition_ptr"]
        self.is_module_private = (
            False if "is_module_private" not in objs[2]
            else objs[2]["is_module_private"]
        )
        self.is_complete_definition = (
            False if "is_complete_definition" not in objs[2]
            else objs[2]["is_complete_definition"]
        )
        self.is_dependent_type = (
            False if "is_dependent_type" not in objs[2]
            else objs[2]["is_dependent_type"]
        )
        return


class EnumConstantDecl(ValueDecl):

    def __init__(self):
        ValueDecl.__init__(self)
        self.init_expr = None
        return

    @staticmethod
    def load_json(objs: list) -> "EnumConstantDecl":
        out = EnumConstantDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        ValueDecl.load_data(self, objs[1])
        self.init_expr = Stmt(
            None if "init_expr" not in objs[2]
            else objs[2]["init_expr"]
        )
        return


class IndirectFieldDecl(ValueDecl):
    
    def __init__(self):
        ValueDecl.__init__(self)
        self.decl_refs = []
        return

    @staticmethod
    def load_json(objs: list) -> "IndirectFieldDecl":
        out = IndirectFieldDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        ValueDecl.load_data(objs[1])
        for dr in objs[2]:
            self.decl_refs.append(DeclRef(dr))
        return


class DeclaratorDecl(ValueDecl):

    def __init__(self):
        ValueDecl.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "DeclaratorDecl":
        out = DeclaratorDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        ValueDecl.load_data(objs[1])
        return


class FunctionDecl(DeclaratorDecl):

    def __init__(self):
        DeclaratorDecl.__init__(self)
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

    @staticmethod
    def load_json(objs: list) -> "FunctionDecl":
        out = FunctionDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        DeclaratorDecl.load_data(self, objs[1])

        data = objs[2]
        self.mangled_name = "" if "mangled_name" not in data else data["mangled_name"]
        self.is_cpp = False if "is_cpp" not in data else data["is_cpp"]
        self.is_inline = False if "is_inline" not in data else data["is_inline"]
        self.is_module_private = False if "is_module_private" not in data else data["is_module_private"]
        self.is_pure = False if "is_pure" not in data else data["is_pure"]
        self.is_delete_as_written = False if "is_delete_as_written" not in data else data["is_delete_as_written"]
        self.is_no_return = False if "is_no_return" not in data else data["is_no_return"]
        self.is_variadic = False if "is_variadic" not in data else data["is_variadic"]
        self.is_static = False if "is_static" not in data else data["is_static"]
        for parm in data["parameters"]:
            self.parameters.append(Decl(parm))
        self.decl_ptr_with_body = None if "decl_ptr_with_body" not in data else data["decl_ptr_with_body"]
        self.body = None if "body" not in data else Stmt(data["body"])
        self.template_specialization = (
                None if "template_specialization" not in data
                else TemplateSpecializationInfo(data["template_specialization"]["template_decl"],
                    data["template_specialization"]["specialization_args"])
        )


class FieldDecl(DeclaratorDecl):

    def __init__(self):
        DeclaratorDecl.__init__(self)
        self.is_mutable = False
        self.is_module_private = False
        self.init_expr = None
        self.bit_width_expr = None
        return

    @staticmethod
    def load_json(objs: list) -> "FieldDecl":
        out = FieldDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        DeclaratorDecl.load_data(objs[1])

        data = objs[2]
        self.is_mutable = False if "is_mutable" not in data else data["is_mutable"]
        self.is_module_private = False if "is_module_private" not in data else data["is_module_private"]
        self.init_expr = None if "init_expr" not in data else Stmt(data["init_expr"])
        self.bit_width_expr = None if "bit_width_expr" not in data else Stmt(data["bit_width_expr"])
        return

class VarDecl(DeclaratorDecl):

    def __init__(self):
        DeclaratorDecl.__init__(self)
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
        self.default = None
        return

    @staticmethod
    def load_json(objs: list) -> "VarDecl":
        out = VarDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        DeclaratorDecl.load_data(self, objs[1])

        data = objs[2]
        self.is_global = False if "is_global" not in data else data["is_global"]
        self.is_extern = False if "is_extern" not in data else data["is_extern"]
        self.is_static = False if "is_static" not in data else data["is_static"]
        self.is_static_local = False if "is_static_local" not in data else data["is_static_local"]
        self.is_static_data_member = (
                False if "is_static_data_member" not in data else
                data["is_static_data_member"]
        )
        self.is_const_expr = False if "is_const_expr" not in data else data["is_const_expr"]
        self.is_init_ice = False if "is_init_ice" not in data else data["is_init_ice"]
        self.init_expr = None if "init_expr" not in data else Stmt(data["init_expr"])
        self.is_init_expr_cxx11_constant = (
                False if "is_init_expr_cxx11_constant" not in data
                else data["is_init_expr_cxx11_constant"]
        )
        self.parm_index_in_function = (
                None if "parm_index_in_function" not in data else
                data["parm_index_in_function"]
        )
        self.default = None if "default" not in data else data["default"]
        return


class UsingDirectiveDecl(NamedDecl):

    def __init__(self):
        NamedDecl.__init__(self)
        self.using_location = None
        self.namespace_key_location = None
        self.nested_name_specifier_locs = []
        self.nominated_namespace = None
        return

    @staticmethod
    def load_json(objs: list) -> "UsingDirectiveDecl":
        out = UsingDirectiveDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamespaceDecl.load_data(self, objs[1])
        self.using_location = SourceLocation(objs[2]["using_location"])
        self.namespace_key_location = SourceLocation(objs[2]["namespace_key_location"])
        for nnsl in objs[2]["nested_name_specifier_locs"]:
            append_this = NestedNameSpecifierLoc()
            append_this.kind = nnsl["kind"]
            append_this.ref = None if "ref" not in nnsl else nnsl["ref"]
            self.nested_name_specifier_locs.append(append_this)
        self.nominated_namespace = (
                None if "nominated_namespace" not in objs[2]
                else objs[2]["nominated_namespace"]
        )
        return


class NamespaceAliasDecl(NamedDecl):

    def __init__(self):
        NamedDecl.__init__(self)
        self.namespace_loc = None
        self.target_name_loc = None
        self.nested_name_specifier_locs = []
        self.namespace = None
        return

    @staticmethod
    def load_json(objs: list) -> "NamespaceAliasDecl":
        out = NamespaceAliasDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamedDecl.load_data(objs[1])
        self.namespace_loc = SourceLocation(objs[2]["namespace_loc"])
        self.target_name_loc = SourceLocation(objs[2]["target_name_loc"])
        for nnsl in objs[2]["nested_name_specifier_locs"]:
            append_this = NestedNameSpecifierLoc()
            append_this.kind = nnsl["kind"]
            append_this.ref = None if "ref" not in nnsl else nnsl["ref"]
        self.namespace = DeclRef(objs[2]["namespace"])
        return


class CXXRecordDecl(RecordDecl):
    
    def __init__(self):
        RecordDecl.__init__(self)
        self.is_polymorphic = False
        self.is_abstract = False
        self.bases = []
        self.transitive_vbases = []
        self.is_pod = False
        self.destructor = None
        self.lambda_call_operator = None
        self.lambda_captures = []
        return

    @staticmethod
    def load_json(objs: list) -> "CXXRecordDecl":
        out = CXXRecordDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        RecordDecl.load_data(self, objs[1])

        data = objs[2]

        self.is_polymorphic = data["is_polymorphic"]
        self.is_abstract = data["is_abstract"]
       
        bases = [] if not "bases" in data else data["bases"]
        for base in bases:
            base_info = baseInfo()
            base_info.type = base["type"]
            base_info.access_spec = base["access_spec"]
            base_info.is_virtual = base["is_virtual"]
            base_info.is_transitive = base["is_transitive"]
            self.bases.append(base_info)

        bases = [] if "transitive_vbases" not in data else data["transitive_vbases"]
        for base_ptr in bases:
            self.transitive_vbases.append(base_ptr)

        self.is_pod = False if "is_pod" not in data else data["is_pod"]
        self.destructor = None if "destructor" not in data else DeclRef(data["destructor"])
        self.lambda_call_operator = (
                None if "lambda_call_operator" not in data else
                DeclRef(data["lambda_call_operator"])
        )
        
        captures = [] if "lambda_captures" not in data else data["lambda_captures"]
        for capture in captures:
            captured = LambdaCaptureInfo()
            captured.capture_kind = capture["capture_kind"]
            captured.capture_this = (
                    False if "capture_this" not in capture else 
                    capture["capture_this"]
            )
            captured.capture_variable = (
                    False if "capture_variable" not in capture else
                    capture["capture_variable"]
            )
            captured.capture_VLAtype = (
                    False if "capture_VLAType" not in capture else
                    capture["capture_VLAType"]
            )
            captured.init_captured_vardecl = (
                    None if "init_captured_vardecl" not in capture else
                    Decl(capture["init_captured_vardecl"])
            )
            captured.is_implicit = (
                    False if "is_implicit" not in capture else
                    capture["is_implicit"]
            )
            captured.location = SourceLocation(capture["location"])
            captured.is_pack_expansion = (
                    False if "is_pack_expansion" not in capture else
                    capture["is_pack_expansion"]
            )
            self.lambda_captures.append(captured)

        return


class ClassTemplateSpecializationDecl(CXXRecordDecl, TemplateSpecialization):

    def __init__(self):
        CXXRecordDecl.__init__(self)
        TemplateSpecialization.__init__(self)
        self.mangled_name = ""
        return

    @staticmethod
    def load_json(objs: list) -> "ClassTemplateSpecializationDecl":
        out = ClassTemplateSpecializationDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        CXXRecordDecl.load_data(self, objs[1])
        self.mangled_name = objs[2]
        TemplateSpecialization.load_data(self, objs[3])
        return


class CXXMethodDecl(FunctionDecl):

    def __init__(self):
        FunctionDecl.__init__(self)
        self.is_virtual = False
        self.is_static = False
        self.is_constexpr = False
        self.cxx_ctor_initializers = []
        self.overriden_methods = []
        return

    @staticmethod
    def load_json(objs: list) -> "CXXMethodDecl":
        out = CXXMethodDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        FunctionDecl.load_data(self,objs[1])

        data = objs[2]
        self.is_virtual = (
                False if "is_virtual" not in data else
                data["is_virtual"]
        )
        self.is_static = (
                False if "is_static" not in data else
                data["is_static"]
        )
        self.is_constexpr = (
                False if "is_constexpr" not in data else
                data["is_constexpr"]
        )

        ctor_initializers = (
                [] if "cxx_ctor_initializers" not in data else
                data["cxx_ctor_initializers"]
        )
        for ctor_init in ctor_initializers:
            append_this = CXXCtorInitializer()

            variant = ctor_init[0]
            if variant == "Member":
                append_this.cxx_ctor_initializer_subject = \
                        DeclRef(ctor_init[1][0])
            elif variant == "Delegating":
                append_this.cxx_ctor_initializer_subject = \
                        ctor_init[1][0]
            elif variant == "BaseClass":
                append_this.cxx_ctor_initializer_subject = \
                        ctor_init[1]
            append_this.source_range = SourceRange.load_json(
                    ctor_init["source_range"])
            append_this.init_expr = (
                    None if "init_expr" not in ctor_init else
                    Stmt(ctor_init)
            )

        overrides = (
                [] if "overriden_methods" not in objs[2] else
                objs[2]["overriden_methods"]
        )
        for override in overrides:
            append_this = DeclRef(override)
            self.overriden_methods.append(append_this)

        return


class CXXConstructorDecl(CXXMethodDecl):

    def __init__(self):
        CXXMethodDecl.__init__(self)
        self.is_default = False
        self.is_copy_ctor = False
        self.is_move_ctor = False
        self.is_converting_ctor = False
        return

    @staticmethod
    def load_json(objs: list) -> "CXXConstructorDecl":
        out = CXXConstructorDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        CXXMethodDecl.load_data(objs[1])
       
        data = objs[2]
        self.is_default = data["is_default"]
        self.is_copy_ctor = data["is_copy_ctor"]
        self.is_move_ctor = data["is_move_ctor"]
        self.is_converting_ctor = data["is_converting_ctor"]

        return


class TemplateDecl(NamedDecl):

    def __init__(self):
        NamedDecl.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "NamedDecl":
        out = TemplateDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamedDecl.load_data(self, objs[1])
        return


class RedeclarableTemplateDecl(TemplateDecl):

    def __init__(self):
        TemplateDecl.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "RedeclarableTemplateDecl":
        out = RedeclarableTemplateDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TemplateDecl.load_data(self, objs[1])
        return


class ClassTemplateDecl(RedeclarableTemplateDecl, CXXRecordDecl):

    def __init__(self):
        RedeclarableTemplateDecl.__init__(self)
        CXXRecordDecl.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "ClassTemplateDecl":
        out = ClassTemplateDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        RedeclarableTemplateDecl.load_data(objs[1])



class FunctionTemplateDecl(RedeclarableTemplateDecl, FunctionDecl):

    def __init__(self):
        RedeclarableTemplateDecl.__init__(self)
        FunctionDecl.__init__(self)
        return

    @staticmethod
    def load_json(objs: list) -> "FunctionTemplateDecl":
        out = FunctionTemplateDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        RedeclarableTemplateDecl.load_data(objs[1])
        FunctionDecl.load_data(objs[2])
        TemplateDecl.load_data(objs[3])
        return

class FriendDecl(Decl):

    def __init__(self):
        Decl.__init__(self)
        self.info = None
        return

    @staticmethod
    def load_json(objs: list) -> "FriendDecl":
        out = FriendDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        Decl.load_data(self, objs[1])
        if objs[2][0] == "Type":
            self.info = objs[2][1]
        elif objs[2][0] == "Decl":
            self.info = Decl(objs[2][1])
        return

class TypeAliasDecl(TypedefNameDecl):

    def __init__(self):
        TypedefNameDecl.__init__(self)
        self.underlying_type = None
        self.described_template = None
        return

    @staticmethod
    def load_json(objs: list) -> "TypeAliasDecl":
        out = TypeAliasDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TypedefNameDecl.load_data(self, objs[1])
        self.underlying_type = QualType.load_json(objs[2]["underlying_type"])
        self.described_template = (
                None if "described_template" not in objs[2]
                else objs[2]["described_template"]
        )
        return

class TypeAliasTemplateDecl(TypeAliasDecl):

    def __init__(self):
        TypeAliasDecl.__init__(self)
        self.canonical_decl = -1
        self.parameters = []
        self.member_template_decl = None
        return

    @staticmethod
    def load_json(objs: list) -> "TypeAliasTemplateDecl":
        out = TypeAliasTemplateDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TypeAliasDecl.load_data(objs[1])
        self.canonical_decl = objs[2]["canonical_decl"]

        for p in objs[2]["parameters"]:
            if p[0] == "TemplateTypeParm":
                self.parameters.append(
                        TemplateTypeParmDecl(p[1])
                        )
            elif p[0] == "NonTypeTemplateParm":
                self.parameters.append(
                        NonTypeTemplateParmDecl(p[1])
                        )
            elif p[0] == "TemplateTemplateParm":
                self.parameters.append(
                        TemplateTemplateParmDecl(p[1])
                        )
        self.member_template_decl = (
                None if "member_template_decl" not in objs[2] else
                objs[2]["member_template_decl"]
        )

        return

class ClassTemplatePartialSpecializationDecl(ClassTemplateSpecializationDecl):

    def __init__(self):
        ClassTemplateSpecializationDecl.__init__(self)
        self.name = ""
        return

    @staticmethod
    def load_json(objs: list) -> None:
        out = ClassTemplatePartialSpecializationDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        CXXRecordDecl.load_json(objs[1])
        self.name = objs[2]
        TemplateSpecialization.load_json(objs[3])
        return


class TemplateTypeParmDecl(TypeDecl):

    def __init__(self):
        TypeDecl.__init__(self)
        self.kind = ""
        self.template_decl = -1
        self.with_typename = False
        self.index = -1
        self.depth = -1
        self.has_default = False
        self.is_parameter_pack = False
        self.default = None
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateTypeParmDecl":
        out = TemplateTypeParmDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        TypeDecl.load_data(self, objs[1])
        self.kind = objs[2]["param_type"]
        self.template_decl = objs[2]["template_decl"]
        self.with_typename = objs[2]["with_typename"]
        self.index = objs[2]["index"]
        self.depth = objs[2]["depth"]
        self.has_default = objs[2]["has_default"]
        self.is_parameter_pack = objs[2]["is_parameter_pack"]
        self.default = (
                None if "default" not in objs[2] else
                QualType.load_json(objs[2]["default"])
                )
        return


class NonTypeTemplateParmDecl(DeclaratorDecl):

    def __init__(self):
        DeclaratorDecl.__init__(self)
        self.kind = ""
        self.template_decl = -1
        self.index = -1
        self.depth = -1
        self.has_default = False
        self.is_parameter_pack = False
        self.type = None
        self.default = None
        return

    @staticmethod
    def load_json(objs: list) -> "NonTypeTemplateParmDecl":
        out = NonTypeTemplateParmDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        DeclaratorDecl.load_data(objs[1])
        self.kind = objs[1]["param_type"]
        self.index = objs[1]["index"]
        self.depth = objs[1]["depth"]
        self.has_default = objs[1]["has_default"]
        self.is_parameter_pack = objs[1]["is_parameter_pack"]
        self.type = QualType.load_json(
                objs[1]["type"]
                )
        self.default = (
                None if "default" not in objs[1] else
                Expr(objs[1]["default"])
        )
        return


class TemplateTemplateParmDecl(NamedDecl):

    def __init__(self):
        NamedDecl.__init__(self)
        self.kind = ""
        self.template_decl = -1
        self.index = -1
        self.depth = -1
        self.has_default = False
        self.is_parameter_pack = False
        self.default = None
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateTemplateParmDecl":
        out = TemplateTemplateParmDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        NamedDecl.load_data(self, objs[1])
        data = objs[2]
        self.kind = data["param_type"]
        self.template_decl = data["template_decl"]
        self.index = data["index"]
        self.depth = data["depth"]
        self.has_default = data["has_default"]
        self.is_parameter_pack = data["is_parameter_pack"]
        self.default = (
                None if "default" not in data else
                data["default"]
                )
        return


class BlockDecl(Decl):

    def __init__(self):
        Decl.__init__(self)
        self.parameters = []
        self.is_variadic = False
        self.captures_cxx_this = False
        self.captured_variables = []
        self.body = None
        self.mangled_name = None
        return

    @staticmethod
    def load_json(objs: list) -> "BlockDecl":
        out = BlockDecl()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        Decl.load_data(objs[1])
        data = objs[2]
        for p in data["parameters"]:
            self.parameters.append(Decl.load_json(p))
        self.is_variadic = (
                False if "is_variadic" not in data else
                data["is_variadic"]
                )
        self.captures_cxx_this = (
                False if "captures_cxx_this" not in data else
                data["captures_cxx_this"]
                )
        for v in data["captured_variables"]:
            append_this = BlockCapturedVariable()
            append_this.is_by_ref = (
                    False if "is_by_ref" not in v else
                    v["is_by_ref"]
                    )
            append_this.is_nested = (
                    False if "is_nested" not in v else
                    v["is_nested"]
                    )
            append_this.variable = (
                    None if "variable" not in v else
                    DeclRef(v["variable"])
                    )
            append_this.copy_expr = (
                    None if "copy_expr" not in v else
                    Stmt(v["copy_expr"])
                    )
            self.captured_variables.append(append_this)
        self.body = (
                None if "body" not in data else
                Stmt(data["body"])
                )
        self.mangled_name = (
                None if "mangled_name" not in data else
                data["mangled_name"]
                )
        return

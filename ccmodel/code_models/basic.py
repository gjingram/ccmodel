
class QualType(Object):

    def __init__(self):
        self.type_ptr = -1
        self.type_string = ""
        self.is_const = False
        self.is_volatile = False
        self.is_restrict = False

        return

    @staticmethod
    def load_json(obj: dict) -> "QualType":
        out = QualType()
        out.load_data(obj)
        return out

    def load_data(self, obj: dict) -> None:
        self.type_ptr = obj["type_ptr"]
        self.type_name = obj["type_name"]
        self.is_const = False if "is_const" not in obj else obj["is_const"]
        self.is_restrict = False if "is_restrict" not in obj else obj["is_restrict"]
        self.is_volatile = False if "is_volatile" not in obj else obj["is_volatile"]
        return


class DeclRef(Object):

    def __init__(self):
        self.kind = ""
        self.decl_pointer = -1
        self.name = None
        self.is_hidden = False
        self.qual_type = None
        return

    @staticmethod
    def load_json(obj: dict) -> "DeclRef":
        out = DeclRef()
        out.load_data(obj)
        return out

    def load_data(self, obj: dict) -> None:
        self.kind = obj["kind"]
        self.decl_pointer = obj["decl_pointer"]
        self.name = None if "name" not in obj else obj["name"]
        self.is_hidden = obj["is_hidden"]
        self.qual_type = None if "qual_type" not in obj else QualType.load_json(obj["qual_type"])


class Decl(Object): 

    def __init__(self):
        self.pointer = -1
        self.parent_pointer = None
        self.source_range = None
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

    @classmethod
    def load_json(cls, obj: dict) -> "Decl":
        out = cls()
        out.load_data(obj)
        return out

    def load_data(self, obj: dict) -> None:
        self.pointer = obj["pointer"]
        self.parent_pointer = None if "parent_pointer" not in obj else obj["parent_pointer"]
        self.source_range = SourceRange.load_json(obj["source_range"])
        self.owning_module = None if "owning_module" not in obj else obj["owning_module"]
        self.is_hidden = False if "is_hidden" not in obj else  obj["is_hidden"]
        self.is_implicit = False if "is_implicit" not in obj else obj["is_implicit"]
        self.is_used = False if "is_used" not in obj else obj["is_used"]
        self.is_this_declaration_referenced = (
                False if "is_this_declaration_referenced" not in obj else
                obj["is_this_declaration_referenced"]
        )
        self.is_invalid_decl = (
                False if "is_invalid_decl" not in obj else 
                obj["is_invalid_decl"]
        )
        for attr in self["attributes"]:
            self.attributes.append(Attribute.load_json(attr))
        self.full_comment = (
                None if "full_comment" not in obj else
                Comment.load_json(obj["full_comment"])
        )
        return

class NamedDecl(Object):

    def __init__(self):
        self.name = "" 
        self.qual_name = "" 
        return

    @staticmethod
    def load_json(obj: dict) -> "NamedDecl":
        out = NamedDecl()
        out.load_data(obj)
        return out

    def load_data(self, obj: dict) -> None:
        self.name = obj["name"]
        self.qual_name = obj["qual_name"]
        return


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


class Type(object):

    def __init__(self):
        self.pointer = -1
        self.desugared_type = None
        self.child_info = None  # Takes on QualType, if not None
        self.variant = ""
        return

    @staticmethod
    def load_json_type(objs: list) -> "Type":
        out = Type()
        self.variant = objs[0]
        out.pointer = obj[1]["pointer"]
        out.desugared_type = None if "desugared_type" not in obj[1] else obj[1]["desugared_type"]
        return out

    @staticmethod
    def load_json_type_with_child(objs: list) -> "Type":
        out = Type.load_json_type(objs)
        out.child_info = QualType.load_json(objs[2])
        return out


class Stmt(object):

    def __init__(self):
        self.kind = ""
        self.pointer = -1
        self.source_range = None
        self.children = []
        return

    @classmethod
    def load_json(cls, objs: list) -> "Stmt":
        out = cls()
        out.load_data(objs)
        return out 

    def load_data(self, objs: list) -> None:
        self.kind = objs[0]
        self.pointer = objs[1]["pointer"]
        self.source_range = SourceRange.load_json(objs[1]["source_range"])

        for s in objs[2]:
            self.children.append(Stmt.load_json(s))
        return


class Expr(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.qual_type = None
        self.value_kind = None
        self.object_kind = None
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        self.qual_type = QualType.load_json(objs[2]["qual_type"])
        self.value_kind = (
                None if "value_kind" not in objs[2] else
                objs[2]["value_kind"]
        )
        self.object_kind = (
                None if "object_kind" not in objs[2] else
                objs[2]["object_kind"]
        )
        return


class TemplateInstantiationArgInfo(Object):

    def __init__(self):
        self.kind = ""
        self.info = None
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateInstantiationArgInfo":
        out = TemplateInstantiationArgInfo()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        self.kind = objs[0]
        if self.kind == "Type":
            self.info = QualType.load_json(objs[1])
        elif (
                self.kind == "Declaration" or
                self.kind == "Integral"
            ):
            self.info = objs[1]
        elif self.kind == "Pack":
            self.info = []
            for arg in objs[1]:
                self.info.append(TemplateInstantiationArgInfo.load_json(arg))
        return


class TemplateSpecializationInfo(Object):

    def __init__(self, ptr: int, args: list):
        self.template_decl = ptr
        self.specialization_args = [
                TemplateInstantiationArgInfo(x) for x in args
        ]
        return


class NestedNameSpecifierLoc(Object):

    def __init__(self):
        self.kind = ""
        self.ref = None
        return


class BaseInfo(Object):

    def __init__(self):
        self.type = -1
        self.access_spec = ""
        self.is_virtual = False
        self.is_transitive = False
        return


class LambdaCaptureInfo(Object):

    def __init__(self):
        self.capture_kind = None
        self.capture_this = False
        self.capture_variable = False
        self.capture_VLAtype = False
        self.init_captured_vardecl = None
        self.is_implicit = False
        self.location = None
        self.is_pack_expansion = False
        return


class TemplateArgument(Object):

    def __init__(self):
        self.variant = ""
        self.info = None
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateArgument":
        out = TemplateArgument()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        self.variant = objs[0]

        if self.variant == "Type":
            self.info = QualType.load_json(objs[1])

        if self.variant == "Integral":
            self.info = objs[1]

        if self.variant == "Pack":
            self.info = []
            for targ in objs[1]:
                self.info.append(TemplateArgument(targ))

        return


class TemplateSpecialization(Object):

    def __init__(self):
        self.template_decl = -1
        self.specialization_args = []
        return

    @staticmethod
    def load_json(objs: list) -> "TemplateSpecialization":
        out = TemplateSpecialization()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        self.template_decl = objs[1]["template_decl"]
        sargs = (
                [] if not "specialization_args" in objs[1] else
                objs[1]["specialization_args"]
        )
        for arg in sargs:
            append_this = TemplateArgument(arg)
            self.specialization_args.append(append_this)
        return


class CXXCtorInitializer(Object):

    def __init__(self):
        self.cxx_ctor_initializer_subject = ""
        self.source_range = None                                                                                                            
        self.init_expr = None


class BlockCapturedVariable(object):

    def __init__(self):
        self.is_by_ref = False
        self.is_nested = False
        self.variable = None
        self.copy_expr = None
        return


class SourceLocation(object):

    def __init__(self):
        self.source_file = ""
        self.line = -1
        self.column = -1
        return

class SourceRange(object):

    def __init__(self):
        self.begin = None
        self.end = None
        return

    @staticmethod
    def load_json(objs: list) -> "SourceRange":
        out = SourceRange()
        out.load_data(objs)
        return out

    def load_data(self, objs: list) -> None:
        self.begin = SourceLocation()
        self.begin.source_file = objs[0]["file"]
        self.begin.line = objs[0]["line"]
        self.begin.column = objs[0]["column"]
        
        self.end = SourceLocation()
        self.end.source_file = objs[1]["file"]
        self.end.line = objs[1]["line"]
        self.end.column = objs[1]["column"]
        return


class Comment(object):

    def __init__(self):
        

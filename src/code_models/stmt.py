from .basic import (
        SourceRange,
        Decl,
        Stmt
)


class DeclStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.decls = []
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])

        for s in objs[2]:
            self.decls.append(Decl.load_json(s))

        return


class IfStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.init = None
        self.cond_var = None
        self.cond = -1
        self.then = -1
        self.else_ptr = None
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])

        data = objs[2]

        self.init = (
                None if "init" not in data else
                data["init"]
                )
        self.cond_var = (
                None if "cond_var" not in data else
                data["cond_var"]
                )
        self.cond = data["cond"]
        self.then = data["then"]
        self.else_ptr = (
                None if "else" not in data else
                data["else"]
                )
        return


class SwitchStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.init = None
        self.cond_var = None
        self.cond = -1
        self.body = -1
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        data = objs[2]

        self.init = (
                None if "init" not in data else
                data["init"]
                )
        self.cond_var = (
                None if "cond_var" not in data else
                data["cond_var"]
                )
        self.cond = data["cond"]
        self.body = data["body"]
        return


class Attr(object):

    def __init__(self):
        self.variant = ""
        self.attr = ""
        self.pointer = -1
        self.source_range = None
        return


class AttributedStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.attributes = []
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        for s in objs[2]:
            append_this = Attr()
            append_this.variant = s[0]
            append_this.attr = s[1]["attr"]
            append_this.pointer = s[1]["pointer"]
            append_this.source_range = \
                    SourceRange.load_json(s[1]["source_range"])
            self.attributes.append(append_this)

        return


class LabelStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.name = ""
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        self.name = objs[2]
        return


class GotoStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.label = ""
        self.pointer = -1
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        self.label = objs[2]["label"]
        self.pointer = objs[2]["pointer"]
        return


class CXXCatchStmt(Stmt):

    def __init__(self):
        Stmt.__init__(self)
        self.variable = None
        return

    def load_data(self, objs: list) -> None:
        Stmt.load_data(self, objs[1])
        self.variable = (
                None if "variable" not in objs[2] else
                objs[2]["variable"]
        )
        return


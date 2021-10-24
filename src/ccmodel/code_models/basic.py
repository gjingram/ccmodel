from abc import ABC, abstractmethod
from typing import Optional, Union, List
import ccmodel.__config__.ccmodel_config as ccm_cfg
import os
import pdb

import ccmodel.code_models.pointers as pointers

ccm_cfg.logger.enable("ccmodel")


def register_ptr(ptr: int, variant: "Variant") -> int:
    pointers.pointer_map[ptr] = variant
    return ptr

class JsonWrapper(object):

    def __init__(self, json: dict):
        self._json = json
        return

    def __call__(self) -> dict:
        return self._json

    def __getitem__(self, key: str) -> Union[dict, str, None]:
        out = None
        try:
            out = self._json[key]
            if out == "None":
                return None
            if type(out) is dict:
                out = JsonWrapper(out)
        except KeyError:
            pass
        return out

    def keys(self):
        for key in self._json.keys():
            yield key

    def values(self):
        for val in self._json.values():
            yield val

    def items(self):
        for item in self._json.items():
            yield item


class Variant(ABC):

    def __init__(self):
        super().__init__()
        self.clang_kind = None
        self.kind = ""
        self._json = None
        self._references = []
        self._referenced = False
        self._save = True
        self._parent = None
        return

    @classmethod
    def load_json(
            cls,
            obj: Optional[dict],
            parent: Optional["Variant"] = None) -> "Variant":
        if obj is None:
            return None
        out = None
        data = obj
        if type(obj) is dict:
            data = JsonWrapper(obj)
        if data["skipped"]:
            out = SkippableVariant()
        else:
            out = cls()
        out.load_content(data)
        out._parent = parent
        return out

    @abstractmethod
    def load_content(self,obj: dict) -> dict:
        pass

    def dump_ccms(self) -> dict:
        return self._json()

    def get_qualified_id(self) -> Optional[str]:
        return None

    def get_id(self) -> Optional[str]:
        return None

    def replace_pointers(self) -> None:
        for attr, val in vars(self).items():
            if isinstance(val, pointers.Pointer):
                ptd_to = val()
                if ptd_to is None and not val._none_ptr:
                    ccm_cfg.logger.bind(stage_log=True, color="yellow")\
                            .opt(colors=True)\
                            .warning(
                                    f"Pointer {val._pointer} missing its object\n"
                                    )
                setattr(self, attr, val())
        return


class SkippableVariant(Variant):

    def __init__(self):
        super().__init__()
        self.skipped = False
        self.reason = ""
        return

    def load_content(self, obj: dict) -> dict:
        self.skipped = obj["skipped"]
        if self.skipped:
            self.reason = obj["reason"]
            self.id = Name.load_json(obj["id"])
            self.pointer = register_ptr(obj["pointer"], self)
        return self.skipped == True


class Include(Variant):

    def __init__(self):
        super().__init__()
        self.search_path = ""
        self.file = ""
        return

    def load_content(self, obj: dict) -> dict:
        self.search_path = os.path.normpath(obj["search_path"])
        self.file = os.path.normpath(obj["file"])
        return


class SourceLocation(Variant):

    def __init__(self):
        super().__init__()
        self.line = None
        self.column = None
        return

    def load_content(self, obj: dict) -> None:
        self.line = obj["line"]
        self.column = obj["column"]
        del self.kind
        del self.clang_kind
        return


class SourceRange(Variant):

    def __init__(self):
        super().__init__()
        self.file = None
        self.begin = None
        self.end = None
        return

    def load_content(self, obj: dict) -> None:
        self.kind = "SourceRange"
        self.file = obj["file"]
        self.begin = SourceLocation.load_json(obj["begin"])
        self.end = SourceLocation.load_json(obj["end"])
        return

    def in_file(self, file_req: str) -> bool:
        return self.file == file_req


class Name(Variant):
    
    def __init__(self):
        super().__init__()
        self.name = ""
        self.qual_name = []
        return

    def write_qual_name(self) -> str:
        if self.qual_name is None:
            pdb.set_trace()
        return "::".join(reversed(self.qual_name)).lstrip()

    def write_name(self) -> str:
        return self.name

    def load_content(self, obj: dict) -> dict:
        self.name = obj["name"]
        self.qual_name = obj["qual_name"]
        return obj

    def resolve_names(self) -> None:
        pass

from .pointers import pointer_map
from .basic import (
    Include,
    JsonWrapper
)
from .variants import (
    DeclFactory,
    NamedDecl
)

import orjson as json
import os
from typing import List


class Header(object):

    def __init__(self, ccs_path: str):
        self.file = ""
        self.includes = []
        self.m_time = -1
        self.translation_unit = None

        self._pointer_map = {}
        pointer_map = self._pointer_map

        self.ccs_path = ccs_path
        self.ccs_basename = os.path.basename(ccs_path)

        self.ccs = {}
        self.load_ccs_file()

        self._id_map = {}
        self.build_id_map()
        return

    def __getitem__(self, id_: str) -> "Variant":
        try:
            return self._id_map[id_]
        except KeyError:
            print(f"Identifier {id_} does not exist in {self.ccs_path}")
        return None

    def load_ccs_file(self) -> None:
        with open(self.ccs_path, "rb") as ccs_file:
            self.ccs = JsonWrapper(json.loads(ccs_file.read()))
        self.file = self.ccs["file"]
        self.includes = [
                Include.load_json(x) for x in self.ccs["includes"]
                ]
        self.m_time = self.ccs["m_time"]
        self.translation_unit = (
                DeclFactory.create_variant(self.ccs["translation_unit"])
                )
        return

    def build_id_map(self) -> None:
        for named_decl in [
                x for x in self._pointer_map if 
                isinstance(x, NamedDecl)
                ]:
            self._id_map[named_decl.get_qualified_id()] = named_decl
        return

    def ls(self, print_keys=True) -> List[str]:
        if print_keys:
            for key in self._id_map.keys():
                print(key)
        return list(self._id_map.keys())


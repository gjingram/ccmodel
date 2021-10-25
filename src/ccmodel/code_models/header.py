from .basic import (
    Include,
    JsonWrapper,
    SkippableVariant
)
import ccmodel.code_models.variants as variants
import ccmodel.code_models.pointers as pointers

import orjson as json
import os
from typing import List, Dict


class Header(object):

    def __init__(self, ccs_path: str):
        global pointer_map

        self.file = ""
        self.includes = []
        self.m_time = -1
        self.translation_unit = None
        self.file_loaded = False

        self.ccs_path = ccs_path
        self.ccs_basename = os.path.basename(ccs_path)
        self.ccs = {}
        self.load_ccs_file()

        self._pointer_map = {}
        self._translation_unit_ids = {}
        self._all_ids = {}
        self._type_map = {}

        pointers.pointer_map = {}
        pointers.qual_types = []
        return

    def __getitem__(self, id_: str) -> "Variant":
        try:
            return self._translation_unit_ids[id_]
        except KeyError:
            print(f"Identifier {id_} does not exist in {self.ccs_path}")
        return None

    def parse_translation_unit(self) -> None:
        self.translation_unit = (
                variants.DeclFactory.create_variant(self.ccs["translation_unit"])
                )
        return

    def merge_includes(self, inc: Dict[str, "Header"]) -> None:
        inc_files = [
                x.file for x in self.includes
                ]
        merged = []
        for ptr, variant in pointers.pointer_map.items():
            if (
                    not isinstance(variant, SkippableVariant) or
                    not variant.skipped or
                    variant.id is None
                    ):
                continue
            variant_type = variant.kind
            variant_id = "::".join(reversed(variant.id.qual_name))
            valid_includes = [
                    x for x in inc.values() if
                    x.file in inc_files
                    ]
            for include in valid_includes:
                if (
                        variant_id in include._all_ids and
                        variant_type == 
                        type(include._all_ids[variant_id]).__name__
                        ):
                    pointers.pointer_map[ptr] = include.all_ids[variant_id]
        return

    def resolve_pointers(self) -> None:
        for variant in pointers.pointer_map.values():
            variant.replace_pointers()
        for qt in pointers.qual_types:
            qt.replace_pointers()
        for typedef in pointers.typedefs:
            typedef.link_typedef()
        self._pointer_map = dict(sorted(pointers.pointer_map.items()))
        return

    def build_all_ids_map(self) -> None:
        processed = []
        for named_decl in [
                x for x in pointers.pointer_map.values() if
                isinstance(x, variants.NamedDecl) and
                not type(x) is variants.NamedDecl
                ]:
            if named_decl in processed:
                continue
            named_decl.set_ccm_identifier()
            self._all_ids[named_decl._ccm_identifier] = named_decl
            processed.append(named_decl)
            if isinstance(named_decl, variants.IdContainer):
                named_decl.build_id_map()
        return

    def build_translation_unit_id_map(self) -> None:
        for name, val in self._all_ids.items():
            if isinstance(val._parent, variants.TranslationUnitDecl):
                self._translation_unit_ids[name] = val
        return

    def load_ccs_file(self) -> None:
        try:
            with open(self.ccs_path, "rb") as ccs_file:
                self.ccs = JsonWrapper(json.loads(ccs_file.read()))
            self.file = self.ccs["file"]
            self.includes = [
                    Include.load_json(x) for x in self.ccs["includes"]
                    ]
            self.m_time = self.ccs["m_time"]
            self.file_loaded = True
        except FileNotFoundError:
            self.file_loaded = False
        return

    def extract_translation_unit(self) -> None:
        self.parse_translation_unit()
        self.build_all_ids_map()
        return

    def ls(self, print_keys=True) -> List[str]:
        if print_keys:
            for key, val in self._translation_unit_ids.items():
                print(key)
                if isinstance(val, variants.IdContainer):
                    val.ls()
                else:
                    print(f"- {key}: {type(val).__name__}")
        return list(self._all_ids.keys())

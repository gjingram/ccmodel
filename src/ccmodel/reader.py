from ccmodel.code_models.variants import (
    DeclFactory,
    StmtFactory,
    ExprFactory,
    AttrFactory,
    DeclContext,
    integer_type_widths
)
from ccmodel.code_models.basic import (
    Include,
)
import ccmodel.code_models.pointers as pointers
from ccmodel.utils import files as fs

import os
import time
from typing import List
from ccmodel.code_models.header import Header
import ccmodel.code_models.pointers as pointers
import orjson as json
import pdb


def clear_pointers() -> None:
    pointers.pointer_map = {}
    pointers.qual_types = []
    pointers.short_types = {}
    pointers.typedefs = []
    return

class CcsReader(object):

    def __init__(self, db_path: str):
        self._database = db_path
        return

    def read(self, ccs_file: str) -> Header:
        main_header = Header(
                os.path.join(
                    self._database,
                    ccs_file.lstrip(os.sep)
                    )
                )
        main_includes = []
        for inc in main_header.includes:
            inc_file_dir = os.path.dirname(inc.file)
            inc_file_base = os.path.basename(inc.file)
            inc_path = os.path.join(
                    self._database,
                    inc_file_dir,
                    inc_file_base) + ".ccs"
            include = Header(os.path.join(
                self._database,
                inc_path.lstrip(os.sep)
                )
                )
            if include.file_loaded:
                include.extract_translation_unit()
                main_includes.append(include)
                clear_pointers()
        main_header.extract_translation_unit()
        main_header.merge_includes(main_includes)
        main_header.resolve_pointers()
        main_header.build_translation_unit_id_map()
        return main_header

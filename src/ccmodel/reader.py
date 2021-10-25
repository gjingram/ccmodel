
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
import sys
import time
from typing import List, Optional
from ccmodel.code_models.header import Header
import ccmodel.__config__.ccmodel_config as ccmodel_config
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
        self._database = os.path.abspath(db_path)
        self._ccs_catalogue = {}
        self.build_catalogue()
        self._headers_loaded = {}
        return

    def build_catalogue(self) -> None:
        for root, dirs, files in os.walk(self._database):
            for file_ in files:
                if os.path.basename(file_).endswith(".ccs"):
                    ccs_abspath = os.path.join(
                            root,
                            file_
                            )
                    self._ccs_catalogue[
                            os.path.relpath(
                                ccs_abspath,
                                self._database
                                )
                            ] = ccs_abspath
        return

    def find_ccs(self, ccs_file: str, must_find: bool = True) -> Optional[str]:
        out = []
        for ccs_file_key, path in self._ccs_catalogue.items():
            if ccs_file_key.endswith(ccs_file):
                out.append(path)
        if len(out) > 1:
            ccmodel_config.logger.bind(stage_log=True, color="red").error(
                    f"Requested state file: {ccs_file} is non-unique." +
                    "\n" +
                    f"Please be more specific."
                    )
            sys.exit(-1)
        elif len(out) < 1:
            if must_find:
                ccmodel.config.logger.bind(stage_log=True, color="red").error(
                        f"Requested state file: {ccs_file} cannot be found in" +
                        "\n" +
                        f"the provided database."
                        )
                sys.exit(-1)
            else:
                return None
        else:
            out = out[0]
        return out

    def load_header(
            self,
            ccs_file: str,
            must_find: bool = True) -> Optional[Header]:
        header_path = self.find_ccs(ccs_file, must_find)
        if (
                header_path is None or
                header_path in self._headers_loaded.keys()
                ):
            return None
        loaded_header = Header(header_path)
        self._headers_loaded[header_path] = loaded_header
        return loaded_header

    def read(self, ccs_file: str, must_find: bool = True) -> Optional[Header]:
        main_header = self.load_header(ccs_file, must_find)
        if main_header is None:
            return None
        for inc in main_header.includes:
            inc_file_dir = os.path.dirname(inc.file).lstrip(os.sep)
            inc_file_base = os.path.basename(inc.file)
            inc_path = os.path.join(
                    inc_file_dir,
                    inc_file_base) + ".ccs"
            self.read(inc_path, must_find=False)
        pdb.set_trace()
        main_header.extract_translation_unit()
        main_header.merge_includes(self._headers_loaded)
        main_header.resolve_pointers()
        main_header.build_translation_unit_id_map()
        return main_header

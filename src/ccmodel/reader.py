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
import copy
import cython
import orjson as json
import pdb

input_file = ""
input_kind = ""
includes = []

def clear() -> None:
    pointers.type_map = {}
    pointers.decl_map = {}
    pointers.stmt_map = {}
    pointers.attr_map = {}
    pointers.attr_data = {}
    pointers.decl_data = {}
    pointers.stmt_data = {}
    pointers.type_data = {}
    input_file = ""
    input_kind = ""
    includes = []
    return

def get_includes() -> List[str]:
    return copy.deepcopy(includes)

def clang_read_and_extract(clang_file: str, ccm: "argparse.Namespace") -> None:
    global input_file, input_kind

    tic = time.perf_counter()
    full_file = os.path.join(os.getcwd(), clang_file)
    translation_unit = fs.load_json_file(full_file)
    toc = time.perf_counter()

    if ccm.verbosity > 0:
        print(f"clang_read_and_extract complete in: {toc - tic} [s]")

    return translation_unit

def _key_recurse(content_dict: dict, key: str) -> None:
    if key in content_dict:
        return content_dict[key]
    else:
        for ckey, val in content_dict.items():
            out = _key_recurse(val, key)
            if out:
                return out
    return None


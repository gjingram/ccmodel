from clang import cindex, enumerations
from typing import (
    Dict,
    List,
    Union,
    Optional
)
import os
import graphlib
import pdb

from ..__config__ import clang_config as clang_cfg
from ..__config__ import ccmodel_config as ccm_cfg
from ..utils import summary as sm
from ..utils import file_sys as fs
from ..utils.code_utils import (
    split_scope_list
)

'''
clang -fsyntax-only -Xpreprocessor -detailed-preprocessing-record -Xclang -load -Xclang ../../fb_plugins/libtooling/build/FacebookClangPlugin.dylib -Xclang -plugin -Xclang JsonASTExporter -Xclang -plugin-arg-JsonASTExporter -Xclang  parse_test.json -c /home/gabriel/projects/ccmodel/ccmodel/test/test_hh/parse_test.hh
'''

_index = clang_cfg.clang.cindex.Index.create()

compiler_args = []
exclude_names = []
include_names = {}
working_directory_path = ""
save_dir = ""
save_ext = ".ccms"
unit_name = ""
headers = []
headers_parsed = {}
template_specializations = {}

summary = sm.ParserSummary()
summary.template_specializations = template_specializations

global_ns = None

def set_working_directory(wd: Optional[str]) -> None:
    global working_directory_path
    working_directory_path = (
            wd if wd is not None else os.get_cwd()
    )
    return

def set_save_extension(ext: str) -> None:
    global save_ext
    save_ext = ext
    return

def global_namespace() -> "NamespaceObject":
    global global_ns
    if global_ns:
        return global_ns
    from ..code_models.namespace import NamespaceObject
    global_ns = NamespaceObject(None)
    return global_ns

def set_save_dir(sv: str) -> None:
    global save_dir
    save_dir = sv
    return

def set_unit_name(un: Optional[str]) -> None:
    global unit_name
    unit_name = (
            un if un is not None else
            working_directory_path.split(os.sep)[-1]
    )
    return

def add_header(h: str) -> None:
    headers.append(h)
    return

def add_headers(hs: List[str]) -> None:
    headers.extend(hs)
    return

def set_compiler_args(args: List[str]) -> None:
    compiler_args.extend(args)
    return

def exclude(scoped_id: str) -> None:
    exclude_names.append(scoped_id)
    return

def excludes(scoped_ids: List[str]) -> None:
    exclude_names.extend(scoped_ids)
    return

def get_excludes() -> List[str]:
    return exclude_names

def include(scoped_id: str, acc_spec: str = "PROTECTED") -> None:
    
    id_parts = split_scope_list(scoped_id)
    for part_idx in range(len(id_parts)-1):
        include_names["::".join(id_parts[:part_idx+1])] = {
                "force_search": True,
                "force_parse": False,
                "access_specifier": acc_spec
        }
    include_names[scoped_id] = {
            "force_search": False,
            "force_parse": True,
            "access_specifier": acc_spec
    }

    return

def get_abspath(path_in: str) -> str:
    if not type(path_in) is str:
        raise RuntimeError(f"Input path {path_in} if not a string")
    return os.path.normpath(os.path.join(working_directory_path, path_in))

def process_headers(lheaders: Optional[Union[str, List[str]]] = None) -> None:
    from ..code_models.header import HeaderObject
    global headers

    logger = ccm_cfg.logger.bind(stage_log=True)
    logger.info(f'Processing headers for unit "{unit_name}"')

    parse_headers = None
    if lheaders is None:
        parse_headers = headers
    else:
        parse_headers = lheaders

    lheaders = None
    if type(parse_headers) is str:
        lheaders = get_abspath(parse_headers)
    elif type(parse_headers) is list:
        lheaders = [get_abspath(x) for x in parse_headers]
    else:
        raise RuntimeError(
                "process_headers received non-string header names"
        )

    headers = lheaders
    header_topo_sort = graphlib.TopologicalSorter()
    header_to_node = {}

    for header in lheaders:
        logger.info(f"Parsing {header} includes")
        pdb.set_trace()
        raw_parse = _index.parse(header, args=compiler_args)
        handle_diagnostics(raw_parse.diagnostics)

        header_obj = HeaderObject(header)
        header_obj.unit_headers = headers
        headers_parsed[header] = header_obj
        header_to_node[header_obj] = raw_parse.cursor
        header_obj.handle_includes(raw_parse)

        header_topo_sort.add(header)
        for unit_header in header_obj.summary.unit_headers:
            header_topo_sort.add(header, unit_header)

        header_deps = tuple(header_topo_sort.static_order())
        for ordered_header in header_deps:
            proc_header = headers_parsed[ordered_header]
            proc_header.handle_object = True
            proc_header.handle(header_to_node[proc_header])
            summary.headers[proc_header.header_file] = proc_header.summary

    pdb.set_trace()
    save_all(summary, save_ext)
    return

def save_all(save_dict: Dict[str, "HeaderSummary"], ext: str) -> None:
    return sm.save_summary(save_dict, unit_name + save_ext, save_dir)

def handle_diagnostics(diags) -> None:

    for diag in diags:
        diag_msg = f"{diag.location.file.name}\nline {diag.location.line} column {diag.location.column}\n{diag.spelling}"
        if diag.severity == clang_cfg.clang.cindex.Diagnostic.Warning:
            warn(diag_msg)
        if diag.severity >= clang_cfg.clang.cindex.Diagnostic.Error:
            raise RuntimeError(diag_msg)
    return

def get_header(hfile: str) -> "HeaderObject":
    if hfile in headers_parsed:
        return headers_parsed[hfile]
    from ..code_models.header import HeaderObject
    headers_parsed[hfile] = HeaderObject(hfile)
    return headers_parsed[hfile]

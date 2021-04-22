from clang import enumerations
from typing import (Dict, List, Union)
import os
import graphlib
import pdb

from ..__config__ import clang_config as clang_cfg
from ..__config__ import ccmodel_config as ccm_cfg
from ..code_models import header
from ..utils import summary

HeaderSummary = summary.HeaderSummary
HeaderObject = header.HeaderObject
save_summary = summary.save_summary

from ..utils import file_sys as fs

_index = clang_cfg.clang.cindex.Index.create()

class ClangParseCpp(object):

    def __init__(self, working_dir: str = os.getcwd(), save_dir: str = os.getcwd(),
            unit_name: str = ""):
        self.unit_name = unit_name if unit_name != "" else working_dir.split(os.sep)[-1]
        self.working_directory_path = working_dir
        self.headers = []
        self.exclude_names = []
        self.parse_also = {}
        self.compiler_args = ""
        self.out_dir = self.working_directory_path if save_dir == "" \
                else os.path.join(self.working_directory_path,
                save_dir)
        self.headers_parsed = {}
        return

    def parse_this(self, scoped_id: str) -> None:
        pdb.set_trace()
        id_parts = scoped_id.split("::")
        for part_idx in range(0, len(id_parts)-1):
            self.parse_also["::".join(id_parts[:part_idx+1])] = {
                    "force_search": True,
                    "force_parse": False
                    }
        self.parse_also[scoped_id] = {
                "force_search": False,
                "force_parse": True
                }
        return

    def add_header(self, header: str) -> None:
        self.headers.append(header)
        return

    def set_headers(self, headers: List[str]) -> None:
        self.headers = headers
        return

    def set_compiler_args(self, args: List[str]) -> None:
        self.compiler_args.extend(args)
        return

    def exclude(self, obj: str) -> None:
        self.exclude_names.append(obj)
        return

    def get_excludes(self) -> List[str]:
        return self.exclude_names

    def _get_abspath(self, path_in: str) -> str:
        if not type(path_in) is str:
            raise RuntimeError(f"Input path {path_in} is not a string.")
        return os.path.normpath(os.path.join(self.working_directory_path, path_in))

    def process_headers(self, headers: Union[None, str, List[str]]=None) -> None:
        logger = ccm_cfg.logger.bind(stage_log=True)
        logger.info(f'Processing headers for unit "{self.unit_name}".')

        parse_headers = None
        if headers is None:
            parse_headers = self.headers
        else:
            parse_headers = headers

        if type(parse_headers) is str:
            self.headers = self._get_abspath(parse_headers)
        elif type(parse_headers) is list:
            self.headers = [self._get_abspath(x) for x in parse_headers]
        else:
            raise RuntimeError('HeaderObject.process_headers received non-string header names to process.')

        header_topo_sort = graphlib.TopologicalSorter()
        header_to_node = {}

        for header in self.headers:
    
            logger.info('Parsing header {} includes'.format(header))
            raw_parse = _index.parse(header, args=self.compiler_args.split())
            self.handle_diagnostics(raw_parse.diagnostics)

            header_obj = HeaderObject(raw_parse.cursor, header, self)
            header_obj.unit_headers = self.headers
            self.headers_parsed[header] = header_obj
            header_to_node[header_obj] = raw_parse.cursor
            header_obj.handle_includes(raw_parse)

            header_topo_sort.add(header)
            for unit_header in header_obj.summary.unit_headers:
                header_topo_sort.add(header, unit_header)

        header_deps = tuple(header_topo_sort.static_order())

        save_dict = {}
        for ordered_header in header_deps:
            proc_header = self.headers_parsed[ordered_header]            
            proc_header.handle(header_to_node[proc_header])
            save_dict[proc_header.header_file] = proc_header.summary

        pdb.set_trace()
        self.save_all(save_dict)
        
        return

    def save_all(self, save_dict: Dict[str, 'HeaderSummary']) -> None:
        return save_summary(save_dict, self.unit_name + ".ccms", self.out_dir) 

    def handle_diagnostics(self, diags) -> None:

        for diag in diags:

            diag_msg = "{}\nline {} column {}\n{}".format(str(diag.location.file),
                                                          diag.location.line,
                                                          diag.location.column,
                                                          diag.spelling)

            if diag.severity == clang_cfg.clang.cindex.Diagnostic.Warning:
                raise RuntimeWarning(diag_msg)

            if diag.severity >= clang_cfg.clang.cindex.Diagnostic.Error:
                raise RuntimeError(diag_msg)

        return

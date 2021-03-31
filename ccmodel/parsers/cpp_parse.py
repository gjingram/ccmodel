from clang import enumerations
import typing
import os
import graphlib
import pdb

import illuminate.__config__.clang_config as ilcc
import illuminate.__config__.illuminate_config as ilc
from illuminate.code_models.header import HeaderObject
from illuminate.collections.unit_summary import UnitSummary

from file_sys import cd, get_files_by_ext

_index = ilcc.clang.cindex.Index.create()

class ClangParseCpp(object):

    def __init__(self, working_dir=os.getcwd()):

        self.project_name = ""
        self.project_root_path = ""

        self.__unit_name = ""
        self.working_directory_path = working_dir

        self.headers = []

        self.local_includes = []
        self.extern_includes = []

        self.exclude_names = []
        self.include_names = []
        self.compiler_args = []

        self.complete_header_obj = None

        self.headers_parsed = {}
        self.module_complete_header_name = os.path.join(self.working_directory_path,
                "." + self.unit_name.replace(".", '_') + ".hh")

        self.unit_summaries = []

        self.extern_id_map = {}

        return

    @property
    def unit_name(self) -> str:
        return self.__unit_name

    @unit_name.setter
    def unit_name(self, name: str) -> None:
        self.__unit_name = name
        self.module_complete_header_name = os.path.join(self.working_directory_path,
                "." + self.__unit_name.replace(".", "_") + ".hh")
        return

    def set_headers(self, headers: typing.List[str]) -> None:
        self.headers = headers
        return

    def set_project_root(self, root: str) -> None:
        self.project_root_path = root
        return

    def set_compiler_args(self, args: typing.List[str]) -> None:
        self.compiler_args.extend(args)
        return

    def exclude(self, obj: str) -> None:
        self.exclude_names.append(obj)
        return

    def get_excludes(self) -> typing.List[str]:
        return self.exclude_names

    def include(self, obj: str) -> None:
        self.include_names.append(obj)
        return

    def process_headers(self, logger: 'loguru.Logger', headers: typing.Union[None, str, typing.List[str]]=None) -> None:
        logger.bind(stage_log=True).info('Processing headers for unit: {}'.format(self.unit_name))

        parse_headers = None
        if type(headers) is str or type(headers) is list:
            parse_headers = headers
        else:
            parse_headers = self.headers

        header_topo_sort = graphlib.TopologicalSorter()
        header_to_node = {}

        for header in parse_headers:

                        
            logger.bind(stage_log=True).info('Parsing header {} includes'.format(header))
            raw_parse = _index.parse(header, args=self.compiler_args)
            self.handle_diagnostics(raw_parse.diagnostics)

            header_rel_path = os.path.relpath(header, start=self.project_root_path)

            header_obj = HeaderObject(raw_parse.cursor, header_rel_path, self, \
                    self.project_root_path, self.unit_name)
            header_obj.unit_headers = parse_headers
            self.headers_parsed[header] = header_obj
            header_to_node[header_obj] = raw_parse.cursor

            header_obj.handle_includes(self.project_root_path, self.working_directory_path, raw_parse)

            header_topo_sort.add(header)
            for unit_header in header_obj.summary.unit_headers:
                header_topo_sort.add(header, unit_header)

        header_deps = tuple(header_topo_sort.static_order())

        for ordered_header in header_deps:
            proc_header = self.headers_parsed[ordered_header]            
            proc_header.handle(header_to_node[proc_header])
            self.unit_summaries.append(proc_header.summary)

        return

    def handle_diagnostics(self, diags) -> None:

        for diag in diags:

            diag_msg = "{}\nline {} column {}\n{}".format(str(diag.location.file),
                                                          diag.location.line,
                                                          diag.location.column,
                                                          diag.spelling)

            if diag.severity == ilcc.clang.cindex.Diagnostic.Warning:
                raise RuntimeWarning(diag_msgs)

            if diag.severity >= ilcc.clang.cindex.Diagnostic.Error:
                raise RuntimeError(diag_msg)

        return

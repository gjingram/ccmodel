import argparse
import os
import sys
import asyncio
import copy
import orjson as json
import time
from pathlib import Path
from warnings import warn
from typing import (
    Tuple,
    List
)

import ccmodel.reader as reader
import ccmodel.code_models.pointers as pointers
from ccmodel.code_models.basic import (
    Name,
    Include
)
from ccmodel.code_models.variants import (
    IdContainer
)
from ccmodel.__config__ import (
    clang_config,
    ccmodel_config
)
import ccm_clang_tools.clang_parse as cp
import ccm_clang_tools.utils as ctu

ccm_cl = argparse.ArgumentParser(
        description="CCModel Command Line Interface"
        )
ccm_cl.add_argument(
        "-f",
        "--files",
        nargs="+",
        help="List of files to parse"
        )
ccm_cl.add_argument(
        "-I",
        "--include-paths",
        nargs="?",
        help="List of include paths to pass to clang",
        default=[]
        )
ccm_cl.add_argument(
        "-v",
        "--verbosity",
        help="Set verbosity",
        type=int,
        default=-1
        )
ccm_cl.add_argument(
        "--recursion-level",
        "-rl",
        help="Specify recursion level for parsing",
        type=int,
        default=0
        )
ccm_cl.add_argument(
        "-dir",
        "--out-dir",
        help="Specify the ccm directory",
        default="ccm"
        )
ccm_cl.add_argument(
        "-do",
        "--delete-out",
        help="Delete output directory, if it exists",
        action="store_true"
        )
ccm_cl.add_argument(
        "-d",
        "--use-docker",
        help="Force use of the ccm-clang-tools docker frontend",
        action="store_true",
        default=False
        )
ccm_cl.add_argument(
        "--force",
        help="Force parse all specified files",
        action="store_true",
        default=False
        )
ccm_cl.add_argument(
        "--process-main-includes",
        "-pmi",
        help="Process included files for those files provided",
        action="store_true",
        default=False
        )
ccm_cl.add_argument(
        "--pretty",
        help="Pretty print JSON out",
        action="store_true",
        default=False
        )


class CcmOpt(object):

    def __init__(self):
        self.verbosity = None
        self.out_dir = None
        self.delete_out = False
        self.use_docker = False
        self.force = False
        self.ccm_files = []
        self.pretty = False
        self.include_paths = []
        self.recursion_level = -1
        self.process_main_includes = None
        self.clang_args = []
        return

ccm_opt = CcmOpt()
include_stage = False
main_includes = []

def handle_command_line() -> Tuple[argparse.Namespace, argparse.Namespace]:

    ccm, clang = ccm_cl.parse_known_args()
    ccm_opt.verbosity = ccm.verbosity
    ccm_opt.out_dir = ccm.out_dir
    ccm_opt.delete_out_dir = ccm.delete_out
    ccm_opt.use_docker = ccm.use_docker
    ccm_opt.force = ccm.force
    ccm_opt.ccm_files = ccm.files
    ccm_opt.pretty = ccm.pretty
    ccm_opt.include_paths.extend(ccm.include_paths)
    ccm_opt.recursion_level = ccm.recursion_level
    ccm_opt.process_main_includes = ccm.process_main_includes

    for file_idx in range(len(ccm_opt.ccm_files)):
        if not ccm_opt.ccm_files[file_idx].startswith(os.sep):
            ccm_opt.ccm_files[file_idx] = os.path.join(
                    os.getcwd(), ccm_opt.ccm_files[file_idx]
                    )
    if not ccm_opt.out_dir.startswith(os.sep):
        ccm_opt.out_dir = os.path.join(
                os.getcwd(),
                ccm_opt.out_dir
                )

    ccm_opt.clang_args.extend(clang)
    for path in ccm_opt.include_paths:
        ccm_opt.clang_args.extend(["-I", path])

    globs = [x for x in ccm_opt.ccm_files if "*" in x]
    if len(ccm_opt.ccm_files) == 0 or len(globs):
        ccmodel_config.logger.bind(stage_log=True, color="red").error(
                "No input files specified\n"
                )
        sys.exit(-1)

    return

def set_main_include_paths() -> bool:
    ccm_opt.ccm_files = []
    for main_inc in main_includes:
        search_path = main_inc.search_path
        file_ = main_inc.file
        ccm_opt.ccm_files.append(file_)
    ccm_opt.ccm_files = list(set(ccm_opt.ccm_files))
    return bool(len(ccm_opt.ccm_files))

def call_clang() -> None:

    pre_processing_notification = ""
    if include_stage:
        pre_processing_notification = "Begin processing of main includes\n"
    else:
        pre_processing_notification = "Begin clang preprocessing\n"
        clang_config.use_docker = ccm_opt.use_docker
        clang_config._find_tool()


    ccmodel_config.logger.bind(stage_log=True).info(
            pre_processing_notification
            )

    tic = time.perf_counter()
    if clang_config.tool_type == clang_config.ToolType.DOCKER:
        cp.docker_command(
                ccm_opt.ccm_files,
                ccm_opt.include_paths,
                ccm_opt.out_dir,
                ccm_opt.verbosity > 1,
                ccm_opt.recursion_level,
                ccm_opt.clang_args,
                ccm_opt.pretty
                )
    elif clang_config.tool_type == clang_config.ToolType.PLUGIN:
        cp.command(
                ccm_opt.ccm_files,
                ccm_opt.include_paths,
                ccm_opt.out_dir,
                ccm_opt.verbosity > 1,
                os.path.join(ctu.clang_tool_path, "libtooling"),
                "clang_tool.dylib",
                ccm_opt.recursion_level,
                ccm_opt.clang_args,
                ccm_opt.pretty
                )
    else:
        ccmodel_config.logger.bind(stage_log=True, color="red")\
                .opt(colors=True)\
                .error(
                "Clang tool backend type resolution failed\n"
                )
        sys.exit(-1)
    toc = time.perf_counter()

    ccmodel_config.logger.bind(stage_log=True, color="green")\
            .opt(colors=True)\
            .info(
            f"Clang preprocessing complete in {toc - tic} [s]\n\n"
            )

    return

def get_clang_out() -> None:
    for file_ in ccm_opt.ccm_files:
        clang_out_dir = os.path.join(
                ccm_opt.out_dir,
                os.path.dirname(file_).lstrip(os.sep)
                )
        basename_noext = os.path.basename(file_).split(".")[0]
        clang_name = basename_noext + "-clang.json"
        ccs_name = basename_noext + ".ccs"

        clang_file = os.path.join(
                clang_out_dir,
                clang_name)
        ccs_file = os.path.join(
                clang_out_dir,
                ccs_name)
        yield ccs_file, clang_file, file_
    return

def remove_host(path: str) -> str:
    if path.startswith(os.sep + "host"):
        path_out = os.path.relpath(
                path,
                os.sep + "host"
                )
        path_out = os.sep + path_out
        return os.path.normpath(out)
    return os.path.normpath(path)

def ccm_process() -> None:
    global main_includes

    main_includes = []
    for ccs_file, clang_file, full_file in get_clang_out():

        tic = time.perf_counter()
        m_time = os.path.getmtime(full_file)
        with open(clang_file, "rb") as data_file:
            data = json.loads(data_file.read())

        full_file = remove_host(full_file)

        for inc in data["content"]["includes"]:
            inc["search_path"] = remove_host(inc["search_path"])
            inc["file"] = remove_host(inc["file"])

        out = {
                "file": full_file,
                "includes": data["content"]["includes"],
                "m_time": m_time,
                "translation_unit": data
                }

        main_includes.extend(
                [Include.load_json(x) for x in out["includes"]]
                )
        with open(ccs_file, "wb") as out_file:
            if ccm_opt.pretty:
                out_file.write(
                        json.dumps(
                            out,
                            option=json.OPT_INDENT_2
                        )
                    )
            else:
                out_file.write(
                        json.dumps(
                            out
                            )
                        )
        toc = time.perf_counter()

        ccmodel_config.logger.bind(stage_log=True).info(
                f"{os.path.relpath(full_file)} parsed in {toc - tic} [s]\n"
                )

        os.remove(clang_file)

    return

def check_for_updates() -> None:
    print()
    remove_files = []
    for file_ in ccm_opt.ccm_files:
        basename = os.path.basename(file_)
        ccs_filename = basename.split(".")[0]
        
        ccs_path = os.path.join(
                ccm_opt.out_dir,
                os.path.dirname(file_).lstrip(os.sep),
                ccs_filename)

        if os.path.exists(ccs_path):
            with open(ccs_path, "rb") as ccs_file:
                data = json.loads(ccs_file.read())
            src_mtime = os.path.getmtime(files[0])
            data_mtime = data["m_time"]
            if src_mtime == data_mtime:
                if force:
                    ccmodel_config.logger.bind(stage_log=True).info(
                            f"Force update {files[1]}\n"
                            )
                    continue
                ccmodel_config.logger.bind(stage_log=True).info(
                        f"{files[1]} up-to-date\n"
                        )
                remove_files.append(files)
    print()
    ccm_files = [
            file_ for file_ in ccm_opt.ccm_files if
            file_ not in remove_files
            ]
    return

def main_ccm() -> None:
    call_clang()
    ccm_process()
    return

def make_output_directories() -> None:
    make_dirs = []
    if (
            os.path.exists(ccm_opt.out_dir) and not
            os.path.isdir(ccm_opt.out_dir)
            ):
        ccmodel_config.logger.bind(stage_log=True, color="red")\
                .opt(colors=True)\
                .error(
                f'"{ccm.out_dir}" and is not a directory.\n' +
                " Please delete or relocate.\n"
                )
        sys.exit(-1)
    elif not os.path.exists(ccm_opt.out_dir):
        if (
                ccm_opt.delete_out and not
                include_stage
                ):
            shutil.rmtree(ccm_opt.out_dir)
        make_dirs.append(ccm_opt.out_dir)

    file_dirs = []
    for file_ in ccm_opt.ccm_files:
        out_dir = os.path.join(
                ccm_opt.out_dir,
                os.path.dirname(file_).lstrip(os.sep)
                )
        file_dirs.append(out_dir)
    file_dirs = list(set(file_dirs))

    make_dirs.extend(
            [
                x for x in
                file_dirs if
                not os.path.exists(x)
                ]
            )
    for dir_ in make_dirs:
        if not os.path.exists(dir_):
            Path(dir_).mkdir(parents=True)
    return

def ensure_cleanup() -> None:
    warning_issued = False
    for _, clang_file, _ in get_clang_out():
        if os.path.exists(clang_file):
            if not warning_issued:
                ccmodel_config.logger.bind(stage_log=True, color="orange")\
                        .opt(colors=True)\
                        .warning(
                    "Cleanup detected a raw clang parse output file. \n" +
                    "This suggests the parse run has failed. Please inspect\n" +
                    "output.\n"
                    )
                warning_issued = True
            os.remove(clang_file)
    return

def main() -> None:
    global include_stage

    if ccm_opt.verbosity > 0:
        ccmodel_config.logger.enable("ccmodel")
    check_for_updates()
    if not len(ccm_opt.ccm_files):
        ensure_cleanup()
        return
    make_output_directories()
    main_ccm()
    ensure_cleanup()
    if ccm_opt.process_main_includes and not include_stage:
        include_stage = True
        set_main_include_paths()
        main()
    return

def run_ccm() -> None:
    handle_command_line()
    main()
    print("\n")
    ccmodel_config.logger.bind(stage_log=True, color="green")\
            .opt(colors=True)\
            .info("CCModel parsing complete!\n")
    return

if __name__ == "__main__":
    run_ccm()

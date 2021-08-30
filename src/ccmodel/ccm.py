import argparse
import os
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
    Name
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

ccm_root = ""
ccm_files = []
include_paths = []
verbosity = -1
out_dir = ""
use_docker = False
force = False
file_base = ""
pretty = False
recursion_level = 0

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
        "-b",
        "--file-base",
        help="Interpret file names as being relative to this",
        default=os.getcwd()
        )
ccm_cl.add_argument(
        "--pretty",
        help="Pretty print JSON out",
        action="store_true",
        default=False
        )

full_paths = []
rel_paths = {}
clang_args = []


def handle_command_line() -> Tuple[argparse.Namespace, argparse.Namespace]:

    global ccm_root, ccm_files, verbosity, out_dir, use_docker, force
    global file_base, pretty

    ccm, clang = ccm_cl.parse_known_args()
    verbosity = ccm.verbosity
    out_dir = ccm.out_dir
    use_docker = ccm.use_docker
    force = ccm.force
    file_base = ccm.file_base
    ccm_files = ccm.files
    pretty = ccm.pretty
    include_paths.extend(ccm.include_paths)
    recursion_level = ccm.recursion_level

    for file_ in ccm_files:
        full_path = os.path.join(
                file_base,
                file_
                )
        full_paths.append(full_path)
        rel_paths[full_path] = file_

    clang_args.extend(clang)
    for path in include_paths:
        clang_args.extend(["-I", path])

    ccm_root = os.path.join(
            os.getcwd(),
            ccm.out_dir
            )

    return

def call_clang() -> None:

    if verbosity >= 0:
        print("Begin clang preprocessing")

    clang_config.use_docker = use_docker
    clang_config._find_tool()

    tic = time.perf_counter()
    if clang_config.tool_type == clang_config.ToolType.DOCKER:
        cp.docker_command(
                ccm_files,
                include_paths,
                file_base,
                None,
                verbosity > 1,
                recursion_level,
                clang_args,
                True,
                False
                )
    elif clang_config.tool_type == clang_config.ToolType.PLUGIN:
        cp.command(
                ccm_files,
                include_paths,
                file_base,
                None,
                verbosity > 1,
                os.path.join(ctu.clang_tool_path, "libtooling"),
                "clang_tool.dylib",
                recursion_level,
                clang_args,
                True,
                False
                )
    else:
        raise RuntimeError("Clang tool backend type resolution failed")
    toc = time.perf_counter()

    if verbosity >= 0:
        print(f"Clang preprocessing complete in: {toc - tic} [s]")

    return

def get_clang_out() -> None:
    for full_path, rel_file in rel_paths.items():
        out_dir = os.path.dirname(full_path)
        basename_noext = os.path.basename(rel_file).split(".")[0]

        clang_name = basename_noext + "-clang.json"
        ccs_name = basename_noext + ".ccs"

        clang_file = os.path.join(out_dir, clang_name)
        ccs_file = os.path.join(
                ccm_root,
                os.path.dirname(rel_file),
                ccs_name
                )
        if os.path.exists(clang_file):
            yield ccs_file, clang_file, full_path
    return


def ccm_process() -> None:

    for ccs_file, clang_file, full_file in get_clang_out():
        tic = time.perf_counter()
        m_time = os.path.getmtime(full_file)
        with open(clang_file, "rb") as data_file:
            data = json.loads(data_file.read())

        out = {
                "file": full_file,
                "includes": data["content"]["includes"],
                "m_time": m_time,
                "translation_unit": data
                }
        with open(ccs_file, "wb") as out_file:
            if pretty:
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

        if verbosity >= 0:
            print(f"{os.path.relpath(full_file)} parsed in {toc - tic} [s]")

        reader.clear()
        os.remove(
                clang_file,
                )

    return

def check_for_updates() -> None:
    global ccm_files, full_paths
    remove_files = []
    for file_idx, files in enumerate(rel_paths.items()):
        basename = os.path.basename(files[1])
        ccs_filename = basename.split(".")[0] + ".ccs"
        ccs_path = os.path.join(
                ccm_root,
                os.path.dirname(files[1]),
                ccs_filename
                )
        if os.path.exists(ccs_path):
            with open(ccs_path, "rb") as ccs_file:
                data = json.loads(ccs_file.read())
            src_mtime = os.path.getmtime(files[0])
            data_mtime = data["m_time"]
            if src_mtime == data_mtime:
                if force:
                    print(f"Force update {files[1]}")
                    continue
                print(f"{files[1]} up to date")
                remove_files.append(files)
    ccm_files = [
            file_ for file_ in ccm_files if
            file_ not in
            [x[1] for x in remove_files]
            ]
    full_paths = [
            path for path in full_paths if
            path not in
            [x[0] for x in remove_files]
            ]
    for file_ in remove_files:
        del rel_paths[file_[0]]

    return

def main() -> None:
    call_clang()
    ccm_process()
    return

def make_output_directories() -> None:
    make_dirs = []
    if os.path.exists(ccm_root) and not os.path.isdir(ccm_root):
        raise RuntimeError(
                '"ccm" exists in {ccm.out_dir} and is not a directory.' +
                " Please delete or relocate."
                )
    elif not os.path.exists(ccm_root):
        make_dirs.append(ccm_root)

    file_dirs = [
            os.path.join(ccm_root, os.path.dirname(x)) for
            x in ccm_files
            ]
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
                warn((
                    "Cleanup detected a raw clang parse output file. \n" +
                    "This suggests the parse run has failed. Please inspect\n" +
                    "output."
                    )
                    )
                warning_issued = True
            os.remove(clang_file)
    return

def run_ccm() -> None:
    check_for_updates()
    if not len(ccm_files):
        ensure_cleanup()
        return
    make_output_directories()
    main()
    ensure_cleanup()
    return

if __name__ == "__main__":
    handle_command_line()
    run_ccm()

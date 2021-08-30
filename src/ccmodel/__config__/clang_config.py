import os
import sys
import subprocess
import shutil
import docker
from warnings import warn
from ccm_clang_tools.utils import (
    check_clang_version,
    check_dylib_exists,
    check_source_exists,
    check_make_exists,
    check_docker_exists,
    check_image_exists,
)
import ccm_clang_tools.build_plugin as bp
import ccm_clang_tools.get_docker_image as gdi
import pdb


class ToolType(object):
    PLUGIN = 0
    DOCKER = 1
    INVALID = 2

tool_type = ToolType.INVALID
use_docker = False
def _find_tool():
    global tool_type

    # Check for a built plugin first
    plugin_exists = check_dylib_exists(raise_=False)
    good_clang_version = False
    clang_build_ok = False
    try:
        clang_build_ok = check_clang_version()
        good_clang_version = True
    except RuntimeError:
        clang_build_ok = False
        good_clang_version = False
    has_make = check_make_exists(raise_=False)
    image_exists = check_image_exists(raise_=False) is not None
    source_exists = check_source_exists(raise_=False)
    can_build = (
            clang_build_ok and
            has_make and
            source_exists
            )

    docker_exists = check_docker_exists(raise_=False)
    image_exists = False
    if docker_exists:
        image_exists = check_image_exists(raise_=False) is not None

    if plugin_exists and good_clang_version and not use_docker:
        tool_type = ToolType.PLUGIN
    elif docker_exists and image_exists:
        tool_type = ToolType.DOCKER
    else:
        print("No backend available -- retrieving")
        if can_build and not use_docker:
            print("Building backend clang plugin")
            sys.argv = []
            sys.argv.append("dummy")
            sys.argv.append(
                    f"-j{os.cpu_count()/2}"
                    )
            bp.build_plugin()
            if check_plugin_exists(raise_=False):
                tool_type = ToolType.PLUGIN
        elif docker_exists:
            try:
                gdi.docker_pull_clang_tool(inform=False)
            except:
                if source_exists:
                    gid.docker_build_clang_tool(inform=False)
            if check_image_exists(raise_=False) is not None:
                toolType = ToolType.DOCKER
        else:
            fail_text = """
            Backend retrieval failed because backend dependencies are unmet.
            To build the backend plugin, source code, make, and clang 10 
            development tools are required. Alternatively, a docker container
            can be used, but it doesn't appear that docker is available.
            """
            print(fail_text)
            raise RuntimeError(
                    "Backend dependencies are unmet"
                    )

    return 

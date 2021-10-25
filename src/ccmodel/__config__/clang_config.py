import os
import sys
import subprocess
import shutil
import docker
from warnings import warn
from ccm_clang_tools.utils import (
    check_clang_version,
    check_clang_dev_exists,
    check_dylib_exists,
    check_source_exists,
    check_make_exists,
    check_docker_exists,
    check_image_exists,
)
import ccm_clang_tools.build_plugin as bp
import ccm_clang_tools.get_docker_image as gdi

import ccmodel.__config__.ccmodel_config as ccm_config


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
    good_clang_version = check_clang_version(raise_=False)
    clang_dev_exists = check_clang_dev_exists(raise_=False)
    clang_build_ok = good_clang_version and clang_dev_exists

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
        ccm_config.logger.bind(stage_log=True).info(
                "Plugin backend selected\n"
                )
        tool_type = ToolType.PLUGIN
    elif docker_exists and image_exists:
        ccm_config.logger.bind(stage_log=True).info(
                "Docker backend selected\n"
                )
        tool_type = ToolType.DOCKER
    else:
        ccm_config.logger.bind(stage_log=True).info(
                "No backend available -- retrieving\n"
                )
        if can_build and not use_docker:
            ccm_config.logger.bind(stage_log=True).info(
                    "Building backend clang plugin\n"
                    )
            sys.argv = []
            sys.argv.append("dummy")
            cpu_count = int(os.cpu_count()/2)
            cpu_count = 1 if cpu_count == 0 else cpu_count
            sys.argv.append(
                    f"-j{cpu_count}"
                    )
            bp.build_plugin()
            if check_dylib_exists(raise_=False):
                tool_type = ToolType.PLUGIN
                ccm_config.logger.bind(stage_log=True, color="green")\
                        .opt(colors=True)\
                        .info("Backend plugin successfully built\n")
                print()
        elif docker_exists:
            try:
                gdi.docker_pull_clang_tool(inform=False)
            except:
                if source_exists:
                    gid.docker_build_clang_tool(inform=False)
            if check_image_exists(raise_=False) is not None:
                tool_type = ToolType.DOCKER
                ccm_config.logger.bind(stage_log=True, color="green")\
                        .opt(colors=True)\
                        .info("Docker image successfully retrieved\n")
                print()
        else:
            fail_text = """
            Backend retrieval failed because backend dependencies are unmet.
            To build the backend plugin, source code, make, and clang 10 
            development tools are required. Alternatively, a docker container
            can be used, but it doesn't appear that docker is available.
            """
            ccm_logger.bind(stage_log=True, color="red")\
                    .opt(colors=True)\
                    .info(fail_text + "\n")
            sys.exit(-1)
            

    return 

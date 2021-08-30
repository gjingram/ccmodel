import sys
import os
import typing
import traceback
import functools
import orjson as json


class cd(object):
    def __init__(self, cd_to):
        self._cwd = os.getcwd()
        self._go_to = cd_to
        return

    def __enter__(self):
        os.chdir(self._go_to)
        return

    def __exit__(self, exc_type, exc_value, tb):
        os.chdir(self._cwd)
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
        return


def get_files_by_ext(
    ext: str, dir_in: str = os.getcwd(), include_hidden=False
) -> typing.List[str]:

    with cd(dir_in):
        if not include_hidden:
            out = [
                ext_file
                for ext_file in os.listdir()
                if ext_file.endswith(ext) and not ext_file.startswith(".")
            ]
        else:
            out = [ext_file for ext_file in os.listdir() if ext_file.endswith(ext)]

    return out

def load_json_file(file_name: str) -> dict:
    content = None
    with open(file_name, "r") as json_file:
        content = json.loads(json_file.read())
    return content

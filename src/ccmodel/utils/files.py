import sys
import os
import typing
import traceback
import functools
import orjson as json


def load_json_file(file_name: str) -> dict:
    content = None
    with open(file_name, "r") as json_file:
        content = json.loads(json_file.read())
    return content

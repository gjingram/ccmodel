import sys
import pathlib
import os
from loguru import logger
from warnings import warn

ccmodel_top = str(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parents[0])

def log_parsed_objects(record):
    return record["extra"]["log_parsed"] and record["extra"]["logs_parses"]

def log_object_dependencies(record):
    return record["extra"]["log_object_deps"] and record["extra"]["logs_object_deps"]

def ccmodel_stage_log(record):
    return record["extra"]["stage_log"]

ccmodel_stage_fmt = "Illuminate: {message}"
ccmodel_common_fmt = "Illuminate: {extra[project]}:{extra[package]}:{extra[header]} -- {message}"

class IndentingParseFormatter(object):

    def __init__(self):
        self.n_spaces = 3
        self.indent_level = 0
        self.fmt = "Illuminate: {extra[header]} -- " + "{extra[indent]}++{message}\n"
        return

    def format(self, record):
        record["extra"]["indent"] = self.indent_level * self.n_spaces * " "
        return self.fmt

indenting_formatter = IndentingParseFormatter()

ccmodel_log_config = {
        "handlers": [
            {"sink": sys.stdout, "format": ccmodel_stage_fmt, "filter": ccmodel_stage_log},
            {"sink": sys.stdout, "format": indenting_formatter.format, "filter": log_parsed_objects},
            {"sink": sys.stdout, "format": indenting_formatter.format, "filter": log_object_dependencies},
            ],
        "extra": {
            "project": "",
            "package": "",
            "header": "",
            "indent": "",
            "log_parsed": False,
            "logs_parses": False,
            "log_object_deps": False,
            "logs_object_deps": False,
            "log_module_deps": False,
            "logs_module_deps": False,
            "log_package_deps": False,
            "logs_package_deps": False,
            "stage_log": False
            }
        }

logger.configure(**ccmodel_log_config)
logger.disable("ccmodel")
object_registry = []
logger_registry = {}

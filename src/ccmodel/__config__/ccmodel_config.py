import sys
import pathlib
import os
from loguru import logger
from warnings import warn

ccmodel_top = str(
        pathlib.Path(
            os.path.dirname(
                os.path.realpath(
                    __file__)
                )
            ).parents[0]
        )

def log_parsed_objects(record):
    return record["extra"]["log_parsed"]

def ccmodel_stage_log(record):
    return record["extra"]["stage_log"]

def ccmodel_stage_fmt(record):
    color = record["extra"]["color"]
    fmt = "ccmodel: {message}"
    if color != "":
        fmt = f"<{color}>" + fmt + f"</{color}>"
    return fmt

class IndentingParseFormatter(object):
    def __init__(self):
        self.n_spaces = 2
        self.indent_level = 0
        self.fmt = (
                "ccmodel: {extra[header]} -- " + "{extra[indent]}|-{message}\n"
                )
        return

    def format(self, record):
        record["extra"]["indent"] = self.indent_level * self.n_spaces * " "
        return self.fmt


indenting_formatter = IndentingParseFormatter()

ccmodel_log_config = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": ccmodel_stage_fmt,
            "filter": ccmodel_stage_log
        },
        {
            "sink": sys.stdout,
            "format": indenting_formatter.format,
            "filter": log_parsed_objects,
        }
    ],
    "extra": {
        "header": "",
        "indent": "",
        "log_parsed": False,
        "stage_log": False,
        "color": ""
    },
}

logger.configure(**ccmodel_log_config)
logger.disable("ccmodel")

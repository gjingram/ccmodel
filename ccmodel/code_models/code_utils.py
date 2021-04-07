from clang import cindex
import typing
from ..__config__ import ccmodel_config as ccm_cfg
import re
import pdb

def add_to_list(list_in: typing.List['ParseObject'], obj: typing.Any, check_instance: typing.Type) -> None:
    if isinstance(obj, check_instance):
        list_in.append(obj)
        return
    if isinstance(obj, list):
        for elem in obj:
            if isinstance(elem, check_instance):
                list_in.append(elem)
            else:
                raise RuntimeError("Input object is expected to be an instance of {}".format(check_instance.__name__))
        return
    raise RuntimeError("Input object is expected to be an instance of {}".format(check_instance.__name__))


def get_relative_id(scope_node: 'cindex.Cursor', obj_node: 'cindex.Cursor', start_name) -> str:
    if scope_node is None or scope_node.kind == cindex.CursorKind.TRANSLATION_UNIT or scope_node is obj_node:
        return start_name
    else:
        return get_relative_id(scope_node, obj_node.semantic_parent, obj_node.spelling + "::" + start_name)

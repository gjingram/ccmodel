import typing
import illuminate.__config__.illuminate_config as il_cfg
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


def get_relative_id(scope_obj: 'ScopingObject', scope_name: str, id_use: str) -> str:
    print(scope_obj.get_name())
    if scope_name == scope_obj.get_name() or scope_obj.get_name() == "GlobalNamespace" or scope_obj.get_name() == "":
        return id_use
    else:
        return get_relative_id(scope_obj.scope, scope_name, scope_obj.get_name() + "::" + id_use)

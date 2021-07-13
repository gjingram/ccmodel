from clang import cindex, enumerations
import typing
import functools

default_code_models = {}
object_code_models = {}


def use_code_model(
    node_kind: typing.Union[str, int], parse_object_type: typing.Type
) -> None:
    if type(node_kind) is not str and node_kind != "comment" and node_kind != "header":
        default_code_models[node_kind] = parse_object_type
    else:
        object_code_models[object_name] = parse_object_type
    return


def default_code_model(node_kind: typing.Union[str, cindex.CursorKind]):
    def _decorator_internal(cls_in):
        default_code_models[node_kind] = cls_in
        return cls_in

    return _decorator_internal

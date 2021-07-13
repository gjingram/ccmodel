from clang import cindex
import typing
from ..__config__ import ccmodel_config as ccm_cfg
import regex
import pdb

template_arglist = r"(?P<match>(?P<t_name>(?::{2})?\w*(?::{2}~?\w*)*[^<])"
template_arglist += r"(?P<t_section>\s*<\s*(?P<t_arglist>.*)\s*>\s*))"
re_targlist = regex.compile(template_arglist)

function_arglist = r"(?P<match>(?P<f_name>(?::{2})?\w*(?::{2}\w*)*[^(])"
function_arglist += r"(?P<a_section>\((?P<f_arglist>.*)\)))"
re_farglist = regex.compile(function_arglist)

iso = r"[\<\[\({,]?\s*(?P<iso>(?:type-parameter-(?:.-.-?)*)"
iso += r"|\w*)\s*[\>\]\)},]?"
re_iso = regex.compile(iso)


def add_to_list(
    list_in: typing.List["ParseObject"], obj: typing.Any, check_instance: typing.Type
) -> None:
    if isinstance(obj, check_instance):
        list_in.append(obj)
        return
    if isinstance(obj, list):
        for elem in obj:
            if isinstance(elem, check_instance):
                list_in.append(elem)
            else:
                raise RuntimeError(
                    "Input object is expected to be an instance of {}".format(
                        check_instance.__name__
                    )
                )
        return
    raise RuntimeError(
        "Input object is expected to be an instance of {}".format(
            check_instance.__name__
        )
    )


def get_relative_id(
    scope_node: "cindex.Cursor", obj_node: "cindex.Cursor", start_name
) -> str:
    if (
        scope_node is None
        or scope_node.kind == cindex.CursorKind.TRANSLATION_UNIT
        or scope_node is obj_node
    ):
        return start_name
    else:
        return get_relative_id(
            scope_node, obj_node.semantic_parent, obj_node.spelling + "::" + start_name
        )


def replace_template_params(obj: "ParseObject") -> None:
    if len(obj["template_parents"]) == 0:
        return
    obj["scoped_displayname"] = replace_template_params_str(
        obj["scoped_displayname"], obj["template_parents"]
    )
    obj.template_params_replaced = True
    return


def replace_template_params_str(
    rep_str: str, parents: typing.List["TemplateObject"]
) -> str:

    if len(parents) == 0:
        return rep_str

    rparams = []
    for parent in parents:
        rparams.extend(
            [
                (x.get_name(), x["parameter"])
                for x in parent["template_parameters"].values()
            ]
        )

    replace_matches = []
    matches = re_iso.finditer(rep_str)
    for match in matches:
        if "iso" in match.groupdict() and match.groupdict()["iso"] is not None:
            iso_val = match.group("iso")
            for rparam in rparams:
                if rparam[0] == iso_val or "type-parameter" in iso_val:
                    replace_matches.append((match, rparam[1]))
                    break

    chars_removed = 0
    for rmatch in replace_matches:
        start = rmatch[0].start("iso")
        end = rmatch[0].end("iso")
        len_rep = end - start
        len_sym = len(rmatch[1])
        rep_str = (
            rep_str[: (start - chars_removed)]
            + rmatch[1]
            + rep_str[(end - chars_removed) :]
        )
        chars_removed += len_rep - len_sym

    return rep_str


def split_bracketed_list(args_in: str, brack: str = "<>", blevel: int = -1) -> typing.List[str]:
    bracket_level = blevel
    str_buffer = []
    out = []
    for char in args_in:
        if bracket_level == 0 and char == ",":
            out.append("".join(str_buffer).strip())
            str_buffer = []
            continue
        if char == brack[0] :
            bracket_level += 1
        if char == brack[1]:
            bracket_level -= 1
        if bracket_level >= 0:
            if bracket_level == 0 and char == brack[0]:
                continue
            str_buffer.append(char)
    out.append("".join(str_buffer).strip())
    return out

def split_scope_list(scoped_name: str) -> typing.List[str]:
    bracket_level = 0
    str_buffer = []
    out = []
    name_len = len(scoped_name)
    char_idx = 0
    while char_idx < name_len-1:
        char = scoped_name[char_idx]
        charp1 = scoped_name[char_idx+1]
        if bracket_level == 0 and char == ":" and charp1 == ":":
            out.append("".join(str_buffer).strip())
            char_idx += 2
            str_buffer = []
            continue
        if char in ['<', '{', '(', '[']:
            bracket_level += 1
        if char in ['>', '}', ')', ']']:
            bracket_level -= 1
        str_buffer.append(char)
        char_idx += 1
    str_buffer.append(scoped_name[-1])
    out.append("".join(str_buffer).strip())
    return out

def find_template_defs(string: str) -> typing.List[str]:
    bracket_level = 0
    str_buffer = []
    out = []
    for char in string:
        str_buf_string = "".join(str_buffer)
        if str_buf_string.startswith("template") and str_buf_string.endswith(">") and \
                bracket_level == 0:
            out.append(str_buf_string)
            str_buffer = []
            continue
        if char == "<":
            bracket_level += 1
        if char == ">":
            bracket_level -= 1
        str_buffer.append(char)
    return out


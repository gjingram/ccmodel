from clang import cindex, enumerations
import functools
import typing
import pdb
import warnings

from ..__config__ import ccmodel_config as ccm_cfg
from ..utils.code_utils import replace_template_params

using_existing_ns = False


def if_handle(method):
    @functools.wraps(method)
    def _if_handle(self, node: cindex.Cursor) -> typing.Union["ParseObject", None]:

        global using_existing_ns
        if self.handle_object or self.force_search:
            indented = False
            if (
                not (self["header"].header_file, self["line_number"], self["scoped_id"])
                in ccm_cfg.object_registry
            ):
                ccm_cfg.indenting_formatter.indent_level += 1
                indented = True
                self.object_logger.info(
                    "Parsing line: {} -- {}".format(
                        self["line_number"], self["scoped_id"]
                    )
                )
                ccm_cfg.object_registry.append(
                    (self["header"].header_file, self["line_number"], self["scoped_id"])
                )

            out = None
            if (
                node.get_usr() in self["header"].summary.usr_map
                and node.kind == cindex.CursorKind.NAMESPACE
                and not using_existing_ns
            ):
                using_existing_ns = True
                obj_use = self["header"].get_usr(node.get_usr())
                out = obj_use.handle(node)
            else:
                out = method(self, node)
                using_existing_ns = False

            if indented:
                ccm_cfg.indenting_formatter.indent_level -= 1

            return out

        return None

    return _if_handle


def add_obj_to_header_summary(obj: "ParseObject") -> None:
    anonymous_not_fparam = obj["is_anonymous"] and not obj["is_fparam"]
    if obj["header"] is not None and not anonymous_not_fparam:
        header_add_fun = None
        try:
            header_add_fn = obj["header"].header_add_fns[obj["kind"]]
        except KeyError:
            header_add_fn = obj["header"].header_add_unknown
        if not obj.is_tparam:
            replace_template_params(obj)
        header_add_fn(obj)
        obj["header"].summary.add_obj_to_summary_maps(obj)

    return


def append_cpo(method):
    @functools.wraps(method)
    def _append_cpo(self, node: cindex.Cursor) -> None:
        obj = method(self, node)
        if obj is None or obj.is_handled:
            return None
        else:
            obj.is_handled = True
        add_obj_to_header_summary(obj)
        return obj

    return _append_cpo

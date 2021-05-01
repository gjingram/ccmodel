from typing import (
    Optional,
    List,
    Union,
    Tuple,
    Dict,
    Any
)
from warnings import warn
import os
import copy
import pickle
import pdb

from ..__config__ import ccmodel_config as ccm_cfg

def load_summary(
    summary_name: str, loc: str = os.getcwd()
) -> Optional["ParserSummary"]:
    summary_path = os.path.join(loc, summary_name)
    summary_out = None
    logger = ccm_cfg.logger.bind(stage_log=True)
    logger.info(f"Attempting to load parse summary at {summary_path}.")
    try:
        with open(summary_path, "rb") as summary_file:
            summary_out = pickle.load(summary_file)
        logger.info("Successfully loaded parse summary")
    except:
        logger.warn("Failed to load parse summary!")

    return summary_out


def save_summary(
    summary: "ParserSummary", summary_name: str, loc: str = os.getcwd()
) -> None:

    if not os.path.exists(loc):
        os.mkdir(loc)
    summary_path = os.path.join(loc, summary_name)
    with open(summary_path, "wb") as summary_file:
        pickle.dump(summary, summary_file)
    return


class Summary(object):

    def __init__(self):

        self.identifier_map = {}
        self.usr_map = {}
        self.template_specializations = {}

        return

    def __getitem__(self, item: str) -> "ParseObject":
        item_ns = item.replace(" ", "")
        out = None
        if item_ns in self.identifier_map:
            out = self.get_usr(self.identifier_map[item_ns])
        if out is None:
            warn(f"No item in summary: {item}")
        return out

    def get_usr(self, usr: str) -> Optional["ParseObject"]:
        if self.usr_in_summary(usr):
            return self.usr_map[usr]
        return None

    def usr_in_summary(self, usr: str) -> bool:
        return usr in self.usr_map

    def name_in_summary(self, name: str) -> bool:
        return name.replace(" ", "") in self.identifier_map

    def add_partial_specialization(self, qual: str, args: tuple, obj: "ParseObject") -> None:
        consider_qual = self.template_specializations[consider_qual]
        if consider_qual is None:
            return
        if not args in consider_qual:
            consider_qual[args] = obj
        return


class ParserSummary(Summary):

    def __init__(self):
        Summary.__init__(self)
        self.headers = {}
        return

    def merge_parser_summary(self, other: "ParserSummary") -> None:
        for usr, usr_obj in other.usr_map.items():
            if usr not in self.usr_map:
                self.identifier_map[usr_obj["scoped_displayname"]] = usr
                self.usr_map[usr] = usr_obj
        for tkey, tval in other.template_specializations.items():
            if tkey not in self.template_specializations:
                self.template_specializations[tkey] = tval
                continue
            for tvalkey, ttval in tval:
                if tvalkey == "primary":
                    if self.template_specializations[tkey]["primary"] is None:
                        self.template_specializations[tkey]["primary"] = ttval
                    continue
                if tvalkey not in self.template_specializations[tkey]:
                    self.template_specializations[tkey][tvalkey] = ttval
        return

    def _extract_header(self, hd: list) -> None:
        for obj in data:
            if not obj["usr"] in self.usr_map:
                self.identifier_map[obj["scoped_displayname"].replace(' ','')] = obj["usr"]
                self.usr_map[obj["usr"]] = obj
        return

    def merge_header(self, h: "HeaderObject") -> None:
        
        if not h.header_file in self.headers:
            self.headers[h.header_file] = h
        self._extract_header(h.namespaces)
        self._extract_header(h.classes)
        self._extract_header(h.class_members)
        self._extract_header(h.class_ctors)
        self._extract_header(h.class_dtors)
        self._extract_header(h.class_methods)
        self._extract_header(h.class_conversions)
        self._extract_header(h.unions)
        self._extract_header(h.enumerations)
        self._extract_header(h.enum_fields)
        self._extract_header(h.variables)
        self._extract_header(h.functions)
        self._extract_header(h.function_params)
        self._extract_header(h.template_classes)
        self._extract_header(h.template_functions)
        self._extract_header(h.partial_specializations)
        self._extract_header(h.template_template_params)
        self._extract_header(h.template_type_params)
        self._extract_header(h.template_non_type_params)
        self._extract_header(h.typedefs)
        self._extract_header(h.template_aliases)
        self._extract_header(h.using)
        self._extract_header(h.namespaces_aliases)

        for qual in h.template_specializations:
            if qual not in self.template_specializations:
                self.template_specializations[qual] = {}
            for key in h.template_specializations[qual]:
                if key not in self.template_specializations[qual]:
                    self.template_specializations[qual][key] = (
                            h.template_specializations[qual][key]
                    )
        return
   

class HeaderSummary(Summary):
    def __init__(self, parser_summary: "ParserSummary"):
        Summary.__init__(self)

        self.parser_summary = parser_summary
        self.file = ""
        self.path = ""
        self.last_modified = 0
        self.namespaces = []
        self.classes = []
        self.class_members = []
        self.class_ctors = []
        self.class_dtors = []
        self.class_methods = []
        self.class_conversions = []
        self.unions = []
        self.enumerations = []
        self.enum_fields = []
        self.variables = []
        self.functions = []
        self.function_params = []
        self.template_classes = []
        self.template_functions = []
        self.partial_specializations = []
        self.template_template_params = []
        self.template_type_params = []
        self.template_non_type_params = []
        self.typedefs = []
        self.template_aliases = []
        self.using = []
        self.namespace_aliases = []
        self.extern_headers = []
        self.unit_headers = []
        self.long_desc = ""
        self.brief = ""
        self.comments = {}
        self.all_objects = []

    def add_partial_specialization(self, qual: str, args: tuple, obj: "ParseObject") -> None:
        self.add_partial_specialization(qual, args, obj)
        self.parser_summary.add_partial_specialization(qual, args, obj)
        return

    def __getitem__(self, item: str) -> "ParseObject":
        return self.parser_summary[item]

    def get_header_item(self, item: str) -> "ParseObject":
        return Summary.__getitem__(self, item)

    def add_obj_to_summary_maps(self, obj: "ParseObject") -> None:
        
        add_to_parser = True
        if self.usr_in_parser_summary(obj["usr"]):
            add_to_parser = False
            obj = self.parser_summary.get_usr(obj["usr"])

        id_use = obj["scoped_displayname"]
        self.identifier_map[id_use.replace(" ", "")] = obj["usr"]
        self.usr_map[obj["usr"]] = obj
        if not obj in self.all_objects:
            self.all_objects.append(obj)

        if add_to_parser:
            self.parser_summary.identifier_map[id_use.replace(" ", "")] = obj["usr"]
            self.parser_summary.usr_map[obj["usr"]] = obj

        return

    def usr_in_parser_summary(self, usr: str) -> bool:
        return self.parser_summary.usr_in_summary(usr)

    def name_in_parser_summary(self, name: str) -> bool:
        return self.parser.name_in_summary(name)

    def usr_get_original_object(self, usr: str) -> Optional["ParseObject"]:
        if self.usr_in_summary(usr):
            return self.usr_map[usr].definition
        return None

    def get_extern_includes(self) -> List[str]:
        return self.extern_headers

    def get_internal_includes(self) -> List[str]:
        return self.unit_headers

    def get_includes(self) -> List[str]:
        out = self.extern_headers
        out.extend(self.unit_headers)
        return out

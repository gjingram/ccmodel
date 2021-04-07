from typing import (Optional, List, Union,
        Tuple, Dict)
import os
import copy
import pickle
import pdb

from ..__config__ import ccmodel_config as ccm_cfg

def load_summary(summary_name: str, loc: str = os.getcwd()) -> Optional[Dict[str, 'HeaderSummary']]:
    summary_path = os.path.join(loc, summary_name)
    summary_out = None
    logger = ccm_cfg.logger.bind(stage_log=True)
    logger.info(f"Attempting to load parse summary at {summary_path}.")
    try:
        with open(summary_path, 'rb') as summary_file:
            summary_out = pickle.load(summary_file)
        logger.info("Successfully loaded parse summary")
    except:
        logger.warn("Failed to load parse summary!")

    return summary_out

def save_summary(summary: Dict[str, 'HeaderSummary'], summary_name: str, loc: str = os.getcwd()) -> None:
    summary_path = os.path.join(loc, summary_name)
    with open(summary_path, 'wb') as summary_file:
        pickle.dump(summary, summary_file)
    return

class HeaderSummary(object):

    def __init__(self):

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
        self.partial_specializations = []
        self.template_functions = []
        self.template_template_params = []
        self.template_type_params = []
        self.template_non_type_params = []
        self.typedefs = []
        self.template_aliases = []
        self.using = []
        self.namespace_aliases = []
        self.extern_headers = []
        self.unit_headers = []
        self.comments = {}
        self.long_desc = ""
        self.brief = ""
        self.all_objects = []

        self.identifier_map = {}
        self.usr_map = {}

    def __getitem__(self, item: Tuple[str]) -> 'ParseObject':
        if item[0].replace(' ', '') in self.identifier_map:
            return self.get_usr(self.identifier_map[item[0]])
        return None

    def get_usr(self, usr: str) -> Optional['ParseObject']:
        if self.usr_in_summary(usr):
            return self.usr_map[usr]
        return None

    def add_obj_to_summary_maps(self, id_use: str, obj: 'ParseObject') -> None:
        self.identifier_map[id_use.replace(' ', '')] = obj.usr
        self.usr_map[obj.usr] = obj
        return

    def name_in_summary(self, name: str) -> bool:
        return name.replace(' ', '') in self.identifier_map

    def usr_in_summary(self, usr: str) -> bool:
        return usr in self.usr_map

    def get_original_object(self, name: str) -> Optional['ParseObject']:
        if name in self.identifier_map:
            return self.usr_map[self.identifier_map[name]].definition
        return None

    def usr_get_original_object(self, usr: str) -> Optional['ParseObject']:
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

from clang import cindex, enumerations
import functools
import typing

import illuminate.__config__.illuminate_config as il_cfg
from illuminate.code_models.code_utils import get_relative_id

def if_handle(method):

    @functools.wraps(method)
    def _if_handle(self, node: cindex.Cursor) -> typing.Union['ParseObject', None]:

        if self.do_handle(node):
            indented = False            
            if not (self.header.header_file, self.line_number, self.qualified_id) in il_cfg.object_registry:
                il_cfg.indenting_formatter.indent_level += 1
                indented = True
                self.object_logger.info('Parsing line: {} -- {}'.format(self.line_number, self.qualified_id))
                il_cfg.object_registry.append((self.header.header_file, self.line_number, self.qualified_id))

            out = method(self, node)
          
            if indented: 
                il_cfg.indenting_formatter.indent_level -= 1
            
            return out

        return None

    return _if_handle

def append_cpo(method):

    
    @functools.wraps(method)
    def _append_cpo(self, node: cindex.Cursor) -> None:

        from illuminate.code_models.function import FunctionObject
        from illuminate.code_models.member_function import MemberFunctionObject
        from illuminate.code_models.template import TemplateObject
        from illuminate.code_models.namespace import NamespaceObject

        obj = method(self, node)
        if obj is None:
            return None

        id_use = obj.get_name()
        template_fn = False
        template_method = False
        if isinstance(obj, TemplateObject):
            append = "<" + ", ".join([x.id for x in obj.template_parameters]) + ">"
            id_use += append
            template_fn = isinstance(obj.obj, FunctionObject)
            template_method = isinstance(obj.obj, MemberFunctionObject)
        if isinstance(obj, FunctionObject) or template_fn:
            append = "(" + ", ".join([x.type for x in obj.info["args"].values()]) + ")"
            id_use += append
        if (isinstance(obj, MemberFunctionObject) or template_method) \
                and obj.is_const:
            id_use += " const"
       
        if isinstance(self, NamespaceObject):
            name_use = get_relative_id(obj.scope, self.get_name(), id_use)
            self.identifier_map[id_use] = obj.usr
            self.usr_map[obj.usr] = obj
            self.all_objects.append(obj)

        if obj.header is not None:
            try:
                header_add_fn = obj.header.header_add_fns[obj.kind]
                header_add_fn(obj)

                header.summary.identifier_map[obj.qualified_id] = obj.usr
                header.summary.usr_map[obj.usr] = obj
            except:
                pass

        return obj

    return _append_cpo

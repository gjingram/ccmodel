from clang import cindex, enumerations
import functools
import typing
import pdb
import warnings

from ..__config__ import ccmodel_config as ccm_cfg
from .code_utils import get_relative_id

def if_handle(method):

    @functools.wraps(method)
    def _if_handle(self, node: cindex.Cursor) -> typing.Union['ParseObject', None]:

        if self.do_handle(node):
            indented = False            
            if not (self.header.header_file, self.line_number, self.scoped_id) in ccm_cfg.object_registry:
                ccm_cfg.indenting_formatter.indent_level += 1
                indented = True
                self.object_logger.info('Parsing line: {} -- {}'.format(self.line_number, self.scoped_id))
                ccm_cfg.object_registry.append((self.header.header_file, self.line_number, self.scoped_id))

            out = method(self, node)
          
            if indented: 
                ccm_cfg.indenting_formatter.indent_level -= 1
            
            return out

        return None

    return _if_handle

def add_obj_to_header_summary(id_use: str, obj: 'ParseObject') -> None:
    if obj.header is not None:
        try:
            header_add_fn = obj.header.header_add_fns[obj.kind]
            header_add_fn(obj)
            obj.header.summary.add_obj_to_summary_maps(id_use, obj)
        except KeyError:
            try:
                warnings.warn(f'no add object fn for cursor {obj.kind.name}')
            except:
                pass

    return

def append_cpo(method):

    
    @functools.wraps(method)
    def _append_cpo(self, node: cindex.Cursor) -> None:

        obj = method(self, node)
        if obj is None:
            return None

        add_obj_to_header_summary(obj.scoped_displayname, obj)
        
        return obj

    return _append_cpo

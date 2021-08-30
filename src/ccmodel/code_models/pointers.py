from typing import Optional
import copy
import pdb

pointer_map = {}

class Pointer(object):

    def __init__(self, ptr: Optional[int], obj: "Variant"):
        obj._references.append(self)
        self._factory = None
        self._pointer = ptr
        return

    def __call__(self) -> "Variant":
        if (
                self._pointer is None or
                not self._pointer in pointer_map
        ):
                return None
        return self.poiner_map[self._pointer]

class_type = {"CONCRETE": 0, "VIRTUAL": 1, "ABSTRACT": 2}
access_spec = {"PRIVATE": 0, "PROTECTED": 2, "PUBLIC": 3, "INVALID": 4, "": 5}


class DependencyType(object):
    EXTERNAL = 0
    INTERNAL = 1
    UNKNOWN = 2

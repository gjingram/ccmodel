from clang import cindex

import illuminate.rules.code_model_map as cmm


@cmm.default_code_model("comment")
class CommentObject(object):

    def __init__(self, tok: cindex.Token):
        self.start_line_number = tok.extent.start.line
        self.end_line_number = tok.extent.end.line
        self.comment = tok.spelling
        return

"""Document Structure Parser.

This module contains a minimal document structure parser. It is meant as a
tmeporary default and will be replaced by more sophisticated parsers and these
parsers will act more liek the other tarsqi components.

Note that the current parser creates elements of TarsqiDocParagraph in the
elements list of the TarsqiDocument. This will be replaced with adding tags just
like all other components, which may mean that the notion of TarsqiDocElement
will be retired.

"""


from docmodel.document import TarsqiDocument
from docmodel.document import TarsqiDocParagraph


class DocumentStructureParser:

    def parse(self, tarsqidoc):
        """Apply a simple default document structure parser to the TarsqiDocument. Sets
        the elements variable of the TarsqiDocument to a list of instances of
        TarsqiDocParagraph, using white lines to separate the paragraphs."""
        self.sourcedoc = tarsqidoc.source
        element_offsets = split_paragraph(self.sourcedoc.text)
        for (p1, p2) in element_offsets:
            para = TarsqiDocParagraph(tarsqidoc, p1, p2)
            para.add_source_tags(self.sourcedoc.tags)
            para.source_tags.index()
            tarsqidoc.elements.append(para)


def split_paragraph(text):
    """Very simplistic way to split a paragraph into more than one paragraph, simply
    by looking for an empty line."""

    text_end = len(text)
    (par_begin, par_end) = (None, None)
    (p1, p2, space) = slurp_space(text, 0)
    par_begin = p2
    seeking_space = False
    paragraphs = []
    
    while (p2 < text_end):
        if not seeking_space:
            (p1, p2, token) = slurp_token(text, p2)
            par_end = p2
            seeking_space = True
        else:
            (p1, p2, space) = slurp_space(text, p2)
            seeking_space = False
            if space.count("\n") > 1:
                par_end = p1
                paragraphs.append((par_begin , par_end ))
                par_begin = p2
                par_end = None

    if seeking_space and p2 > par_begin:
        paragraphs.append((par_begin, par_end))

    # this deals with the boundary case where there are no empty lines, should really have
    # a more elegant solution
    if not paragraphs:
        paragraphs = [(0, text_end)]

    return paragraphs


def slurp(text, offset, test):
    """Starting at offset in text, find a substring where all characters pass test. Return
    the begin and end position and the substring."""
    begin = offset
    end = offset
    length = len(text)
    while offset < length:
        char = text[offset]
        if test(char):
            offset += 1
            end = offset
        else:
            return (begin, end, text[begin:end])
    return (begin, end, text[begin:end])

def slurp_space(text, offset):
    """Starting at offset consume a string of space characters, then return the
    begin and end position and the consumed string."""
    def test_space(char): return char.isspace()
    return slurp(text, offset, test_space)

def slurp_token(text, offset):
    """Starting at offset consume a string of non-space characters, then return
    the begin and end position and the consumed string."""
    def test_nonspace(char): return not char.isspace()
    return slurp(text, offset, test_nonspace)

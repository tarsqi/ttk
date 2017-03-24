"""Document Structure Parser.

This module contains a minimal document structure parser. It is meant as a
temporary default and will be replaced by more sophisticated parsers and these
parsers will act more like the other tarsqi components.

The main goal of the parser is to add docelement tags to the tag repository on
the TarsqiDocument. Sometimes docelement tags already exist in the tag
repository (for example when reading a ttk file), in which case the parser does
nothing. Otherwise, the parser calls a simple method to recognize paragraphs and
creates a docelement Tag for each of them.

The docelements are used by Tarsqi components by looping over them and
processing the elements one by one.

"""


from library.tarsqi_constants import DOCSTRUCTURE
from docmodel.document import TarsqiDocument


class DocumentStructureParser:

    """Simple document structure parser used as a default if no structure tags are
    found in the tag repository of the TarsqiDocument."""

    def parse(self, tarsqidoc):
        """Apply a default document structure parser to the TarsqiDocument if
        there are no docelement tags in the tags repository. The parser uses
        white lines to separate the paragraphs."""
        doc_elements = tarsqidoc.tags.find_tags('docelement')
        if not doc_elements:
            element_offsets = split_paragraphs(tarsqidoc.sourcedoc.text)
            count = 0
            for (p1, p2) in element_offsets:
                count += 1
                pid = "d%s" % count
                feats = {'id': pid, 'type': 'paragraph', 'origin': DOCSTRUCTURE}
                tarsqidoc.tags.add_tag('docelement', p1, p2, feats)


def split_paragraphs(text):
    """Very simplistic way to split a paragraph into more than one paragraph,
    simply by looking for an empty line."""

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
                paragraphs.append((par_begin, par_end))
                par_begin = p2
                par_end = None

    if seeking_space and p2 > par_begin:
        paragraphs.append((par_begin, par_end))

    # this deals with the boundary case where there are no empty lines, should
    # really have a more elegant solution
    if not paragraphs:
        paragraphs = [(0, text_end)]

    return paragraphs


def slurp(text, offset, test):
    """Starting at offset in text, find a substring where all characters pass
    test. Return the begin and end position and the substring."""
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
    def test_space(char):
        return char.isspace()
    return slurp(text, offset, test_space)


def slurp_token(text, offset):
    """Starting at offset consume a string of non-space characters, then return
    the begin and end position and the consumed string."""
    def test_nonspace(char):
        return not char.isspace()
    return slurp(text, offset, test_nonspace)

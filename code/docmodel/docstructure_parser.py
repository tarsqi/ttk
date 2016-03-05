"""Document Structure Parser.

This module contains a minimal document structure parser. It is meant as a
temporary default and will be replaced by more sophisticated parsers and these
parsers will act more like the other tarsqi components.

The main goal of the parser is to initialize the elements list on the
TarsqiDocument and the current parser creates elements of TarsqiDocParagraph in
that list. With a virgin document, these elements will be empty. In that case,
the parser calls a simple method to recognize paragraphs and creates a
TarsqiDocParagraph for each of them, populating it with source_tags from the
SourceDoc (only those that overlap with the paragraph). However, previously
processed documents may already have document structure in doc_element tags and
those will be used to create document elements. In addition, those document
element may already have tarsqi_tags and those will be added.

The elements list is used by Tarsqi components by looping over them and
processingg the elements one by one. Note that the continued existence of the
elements list is under discussion (https://github.com/tarsqi/ttk/issues/2).

One as-of-yet unanswered question now is what to do with tarsqi_tags that do not
fall neatly in of the document elements (that is, TLINKS that cross paragraphs,
see https://github.com/tarsqi/ttk/issues/13).

"""


from docmodel.document import TarsqiDocument
from docmodel.document import TarsqiDocParagraph


class DocumentStructureParser:

    """Simple document structure parser that either takes an existing document
    structure from the source document or uses a simple method to create
    paragraphs from a text string."""

    def parse(self, tarsqidoc):
        """Apply a simple default document structure parser to the TarsqiDocument. It
        sets the elements variable of the TarsqiDocument to a list of instances
        of TarsqiDocParagraph, using either existing document structure in the
        SourceDoc's tarsqi_tags or a simple approach to split paragraphs in the
        SourceDoc text field. """
        self.tarsqidoc = tarsqidoc
        self.sourcedoc = tarsqidoc.source
        doc_elements = self.sourcedoc.tarsqi_tags.find_tags('doc_element')
        if doc_elements:
            self._copy_docstructure(doc_elements)
        else:
            self._create_default_docstructure()

    def _copy_docstructure(self, doc_elements):
        """Copy the document structure from the existing tags in the source document and
        add source_tags and tarsqi_tags to the document elements."""
        for doc_element in doc_elements:
            p1 = int(doc_element.begin)
            p2 = int(doc_element.end)
            para = TarsqiDocParagraph(self.tarsqidoc, p1, p2)
            para.add_source_tags(self.sourcedoc.source_tags)
            para.add_tarsqi_tags(self.sourcedoc.tarsqi_tags)
            para.source_tags.index()
            para.tarsqi_tags.index()
            self.tarsqidoc.elements.append(para)

    def _create_default_docstructure(self):
        """Set the elements variable of the TarsqiDocument to a list of instances of
        TarsqiDocParagraph, using white lines to separate the paragraphs. This
        method assumes that there are no tarsqi tags in the source. """
        element_offsets = split_paragraph(self.sourcedoc.text)
        for (p1, p2) in element_offsets:
            para = TarsqiDocParagraph(self.tarsqidoc, p1, p2)
            para.add_source_tags(self.sourcedoc.source_tags)
            para.source_tags.index()
            self.tarsqidoc.elements.append(para)


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
                paragraphs.append((par_begin, par_end))
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
    def test_space(char):
        return char.isspace()
    return slurp(text, offset, test_space)


def slurp_token(text, offset):
    """Starting at offset consume a string of non-space characters, then return
    the begin and end position and the consumed string."""
    def test_nonspace(char):
        return not char.isspace()
    return slurp(text, offset, test_nonspace)

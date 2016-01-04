"""

This module contains document source parsers. That is, parsers that take an
instance of SourceDoc and create an instance of TarsqiDocument.

"""

import re, time

from docmodel.document import TarsqiDocument
from docmodel.document import TarsqiDocParagraph
import utilities.logger as logger


# Default content tags, used by the default parser to find the part of the text that is
# worth parsing.
CONTENT_TAGS = ('TEXT', 'text', 'DOC', 'doc')


class DefaultParser:

    """The simplest parser, much like the SimpleXml parser for the old simple-xml
    doctype. It creates a TarsqiDocument instance with a list of TarsqiDocParagraphs in
    it. It finds the target tag, which is assumed to be TEXT, and considers all text
    inside as the content of a single TarsqiDocParagraph.

    TODO: figure out exatly what it does with the paragraphs and update the documentation

    TODO: may want to allow the user to hand in a target_tag as a processing parameter,
    thereby bypassing the default list in CONTENT_TAGS. Should include the option to use
    --target_tag=None so that we overrule using any tag (for example for documents with
    lots of TEXT tags, in which case only the first one of those would be used).

    TODO: make this work with pure text input, taking all content, perhaps a default
    should be to take all text if no target tag could be found.
    
    Instance variables:
       sourcedoc - a SourceDoc instance
       elements - a list with TarsqiDocParagraph elements
       metadata - a dictionary"""

    
    def __init__(self, parameters):
        """Not used now but could be used to hand in specific metadata parsers or other
        functionality that cuts through genres."""
        self.content_tag = parameters.get('content_tag', True) 

    def parse(self, sourcedoc):
        """Return an instance of TarsqiDocument. Use self.content_tag to determine what
        part of the source to take and populate the TarsqiDocument with: (i)
        sourcedoc: the SourceDoc instance that was created by the SourceParser,
        (ii) elements: a list of TarsqiDocParagraphs, (iii) metadata: a
        dictionary with now one element, the DCT, which is set to today."""
        self.sourcedoc = sourcedoc
        self.target_tag = self._find_target_tag()
        offset_adjustment = self.target_tag.begin if self.target_tag else 0
        text = self.sourcedoc.text
        if self.target_tag:
            text = self.sourcedoc.text[self.target_tag.begin:self.target_tag.end]
        metadata = { 'dct': self.get_dct() }
        tarsqidoc = TarsqiDocument(self.sourcedoc, metadata)
        element_offsets = split_paragraph(text, offset_adjustment)
        for (p1, p2) in element_offsets:
            para = TarsqiDocParagraph(tarsqidoc, p1, p2)
            para.add_source_tags(self.sourcedoc.tags)
            para.source_tags.index()
            tarsqidoc.elements.append(para)
        return tarsqidoc

    def get_dct(self):
        """Return today's date in YYYYMMDD format."""
        return get_today()
    
    def _find_target_tag(self):
        """Return the Tag that contains the main content that needs to be processed. Any
        text outside of the tag will NOT be processed. Uses the tagnames in CONTENT_TAGS
        or the overide in the self.content_tag, which originated from the user
        parameters. Return None if there is no such tag."""
        if self.content_tag is False:
            return None
        elif self.content_tag is True:
            for tagname in CONTENT_TAGS:
                tag = self.sourcedoc.tags.find_tag(tagname)
                if tag is not None:
                    return tag
            return None
        else:
            return docsource.tags.find_tag(self.content_tag)

    def _get_tag_content(self, tagname):
        """Return the text content of the first tag with name tagname, return None if
        there is no such tag."""
        try:
            tag = self.sourcedoc.tags.find_tags(tagname)[0]
            content = self.sourcedoc.text[tag.begin:tag.end].strip()
            return content
        except IndexError:
            logger.warn("Cannot get the %s tag in this document" % tagname)
            return None


def split_paragraph(text, adjustment=0):
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
                paragraphs.append((par_begin + adjustment, par_end + adjustment))
                par_begin = p2
                par_end = None

    if seeking_space and p2 > par_begin:
        paragraphs.append((par_begin + adjustment, par_end + adjustment))

    # this deals with the boundary case where there are no empty lines, should really have
    # a more elegant solution
    if not paragraphs:
        paragraphs = [(0 + adjustment, text_end + adjustment)]
        
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


class TimebankParser(DefaultParser):
    """The parser for Timebank documents. All it does is overwriting the get_dct()
    method."""
    
    def get_dct(self):
        """Extracts the document creation time, and returns it as a string of the form
        YYYYMMDD. Depending on the source, the DCT can be found in one of the
        following tags: DOCNO, DATE_TIME, PUBDATE or FILEID."""
        result = self._get_doc_source()
        if result is None:
            # dct defaults to today if we cannot find the DOCNO tag in the document
            return get_today()
        source_identifier, content = result
        if source_identifier in ('ABC', 'CNN', 'PRI', 'VOA'):
            return content[3:11]
        elif source_identifier == 'AP':
            dct = self._parse_tag_content("(?:AP-NR-)?(\d+)-(\d+)-(\d+)", 'FILEID')
            # the DCT format is YYYYMMDD or YYMMDD
            return dct if len(dct) == 8 else '19' + dct
        elif source_identifier in ('APW', 'NYT'):
            return self._parse_tag_content("(\d+)/(\d+)/(\d+)", 'DATE_TIME')
        elif source_identifier == 'SJMN':
            pubdate_content = self._get_tag_content('PUBDATE')
            return '19' + pubdate_content
        elif source_identifier == 'WSJ':
            return '19' + content[3:9]
        elif source_identifier in ('ea', 'ed'):
            return '19' + content[2:8]

    def _get_doc_source(self):
        """Return the name of the content provider as well as the content of the DOCNO
        tag that has that information."""
        content = self._get_tag_content('DOCNO')
        content = str(content)  # in case the above returned None
        for source_identifier in ('ABC', 'APW', 'AP', 'CNN', 'NYT', 'PRI', 'SJMN', 'VOA', 'WSJ', 'ea', 'ed'):
            if content.startswith(source_identifier):
                return (source_identifier, content)
        logger.warn("Could not determine document source from DOCNO tag")
        return None

    def _parse_tag_content(self, regexpr, tagname):
        """Return the DCT part of the tag content of tagname, requires a reqular
        expression as one of the arguments."""
        content_string =  self._get_tag_content(tagname)
        result = re.compile(regexpr).match(content_string)
        if result:
            (month, day, year) = result.groups()
            return "%s%s%s" % (year, month, day)
        else:
            logger.warn("Could not get date from %s tag" % tagname)
            return get_today()


class ATEEParser(DefaultParser):
    """The parser for ATEE document."""

    def get_dct(self):
        """All ATEE documents have a DATE tag with a value attribute, the value of that attribute
        is returned."""
        date_tag = self.sourcedoc.tags.find_tag('DATE')
        return date_tag.attrs['value']


class RTE3Parser(DefaultParser):
    """The parser for RTE3 documents, does not differ yet from the default
    parser."""
    
    def get_dct(self):
        return get_today()


def get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime());



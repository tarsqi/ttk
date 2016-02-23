"""parsers.py

This module contains document source parsers, that is, parsers that take an
instance of SourceDoc and create an instance of TarsqiDocument.

The only requirements on each parser is that it defines an __init__() method
that takes a dictionary of parameters and a parse() method that takes a
SourceDoc instance.

"""

import re, time, os, sqlite3

from mixins.parameters import ParameterMixin
from docmodel.document import TarsqiDocument
from docmodel.document import TarsqiDocParagraph
import utilities.logger as logger


class SimpleParser(ParameterMixin):

    """The simplest SourceDoc parser. It creates a TarsqiDocument instance
    with a list of TarsqiDocParagraphs in it."""

    def __init__(self, parameters):
        """At the moment, initialization does not use any of the parameters,
        but this could change."""
        self.paremeters = parameters
        pass

    def parse(self, sourcedoc):
        """Return an instance of TarsqiDocument. The TarsqiDocument includes the
        SourceDoc instance and a meta data dictionary with just one element, the
        DCT, which is set to today. The elements variable of the TarsqiDocument
        is set to a list of TarsqiDocParagraph instances, using white lines to
        separate the paragraphs."""
        self.sourcedoc = sourcedoc
        metadata = { 'dct': self.get_dct() }
        tarsqidoc = TarsqiDocument(self.sourcedoc, metadata)
        element_offsets = split_paragraph(self.sourcedoc.text)
        for (p1, p2) in element_offsets:
            para = TarsqiDocParagraph(tarsqidoc, p1, p2)
            para.add_source_tags(self.sourcedoc.tags)
            para.source_tags.index()
            tarsqidoc.elements.append(para)
        return tarsqidoc

    def get_dct(self):
        """Return today's date in YYYYMMDD format."""
        return get_today()

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


class TimebankParser(SimpleParser):
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


class ATEEParser(SimpleParser):
    """The parser for ATEE document."""

    def get_dct(self):
        """All ATEE documents have a DATE tag with a value attribute, the value of that attribute
        is returned."""
        date_tag = self.sourcedoc.tags.find_tag('DATE')
        return date_tag.attrs['value']


class RTE3Parser(SimpleParser):
    """The parser for RTE3 documents, does not differ yet from the default
    parser."""

    def get_dct(self):
        return get_today()


class VAExampleParser(SimpleParser):

    """A minimal example parser for VA data. It is identical to the SimpleParser
    except for how it gets the DCT. This is done by lookup in a database. This
    here is the simplest possible case, and it is quite inefficient. It assumes
    there is an sqlite databse at 'TTK_ROOT/code/data/in/va/dct.sqlite' which
    was created as follows:

       $ sqlite3 dct.sqlite
       sqlite> create table dct (filename TEXT, dct TEXT)
       sqlite> insert into dct values ("test.xml", "1999-12-31");

    The get_dct method uses this database. """
    
    def get_dct(self):
        fname = self.sourcedoc.filename
        fname = os.path.basename(fname)
        db_connection = sqlite3.connect('data/in/va/dct.sqlite')
        db_cursor = db_connection.cursor()
        db_cursor.execute('SELECT dct FROM dct WHERE filename=?', (fname,))
        dct = db_cursor.fetchone()[0]
        return dct


def get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime());

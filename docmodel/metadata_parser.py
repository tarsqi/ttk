"""Metadata Parsers.

This module contains metadata parsers, that is, parsers that pull out the
metadata and add it to a TarsqiDocument. The only requirements on each parser is
that it defines an __init__() method that takes a dictionary of options and a
parse() method that takes a TarsqiDocument instance.

Current parsers only deal with the DCT.

"""

import re, time, os, sqlite3

from docmodel.document import TarsqiDocument
import utilities.logger as logger
from library.main import LIBRARY


class MetadataParser:

    """This is the minimal metadata parser that is used as a default. It selects
    the DCT from all available sources and picks one of them, or it uses today's
    date if no DCT's are available. Subclasses should override the get_dct()
    method to define specific DCT extraction methods for the document source."""

    def __init__(self, options):
        """At the moment, initialization only uses the --dct option if it is
        present, but this could change. Note that the TarsqiDocument does not
        exist yet when the MetadataParser is initialized."""
        self.options = options
        self.tarsqidoc = None  # added in by the parse() method

    def parse(self, tarsqidoc):
        """Adds metadata to the TarsqiDocument. The only thing it adds to the
        metadata dictionary is the DCT, which is set to today."""
        self.tarsqidoc = tarsqidoc
        self.tarsqidoc.metadata['dct'] = self.get_dct()
        self._moderate_dct_vals()

    def _moderate_dct_vals(self):
        """There are five places where a DCT can be expressed: the DCT handed in
        with the --dct option or defined in the config file, the DCT from the
        metadata on the TarsqiDocument, the DCT from the metadata on the
        SourceDoc, DCTs from the TagRepository on the TarsqiDocument and DCTs
        from the TagRepository on the SourceDoc. The first three are single
        values or None, the other two are lists of any length. The order of
        these five is significant in that a DCT earlier on the list if given
        precedence over a DCT later on the list. Collects all the DCT values and
        picks the very first one, or today's date if no DCTs are available. Logs
        a warning if the DCTs do not all have the same value."""
        dcts = []
        for dct_val in [self.tarsqidoc.options.dct,
                        self.tarsqidoc.metadata.get('dct'),
                        self.tarsqidoc.sourcedoc.metadata.get('dct'),
                        _get_dct_values(self.tarsqidoc.sourcedoc.tags),
                        _get_dct_values(self.tarsqidoc.tags)]:
            if dct_val is None:
                # the case where there is no DCT in the options or metadata
                continue
            elif isinstance(dct_val, list):
                dcts.extend(dct_val)
            else:
                dcts.append(dct_val)
        if len(set(dcts)) > 1:
            logger.warn("WARNING: more than one DCT value available")
        dct = dcts[0] if dcts else _get_today()
        self.tarsqidoc.metadata['dct'] = dct

    def get_dct(self):
        return None

    def _get_source(self):
        """A convenience method to lift the SourceDoc out of the tarsqi
        instance."""
        return self.tarsqidoc.sourcedoc

    def _get_tag_content(self, tagname):
        """Return the text content of the first tag with name tagname, return
        None if there is no such tag."""
        try:
            tag = self._get_source().tags.find_tags(tagname)[0]
            content = self._get_source().text[tag.begin:tag.end].strip()
            return content
        except IndexError:
            logger.warn("Cannot get the %s tag in this document" % tagname)
            return None


class MetadataParserTTK(MetadataParser):

    """The metadata parser for the ttk format. For now this one adds
    nothing to the default metadata parser."""


class MetadataParserText(MetadataParser):

    """The metadata parser for the text format. For now this one adds
    nothing to the default metadata parser."""


class MetadataParserTimebank(MetadataParser):

    """The parser for Timebank documents. All it does is to overwrite the
    get_dct() method."""

    def get_dct(self):
        """Extracts the document creation time, and returns it as a string of
        the form YYYYMMDD. Depending on the source, the DCT can be found in one
        of the following tags: DOCNO, DATE_TIME, PUBDATE or FILEID."""
        result = self._get_doc_source()
        if result is None:
            # dct defaults to today if we cannot find the DOCNO tag in the
            # document
            return _get_today()
        source_identifier, content = result
        if source_identifier in ('ABC', 'CNN', 'PRI', 'VOA'):
            return content[3:11]
        elif source_identifier == 'AP':
            dct = self._parse_tag_content("(?:AP-NR-)?(\d+)-(\d+)-(\d+)",
                                          'FILEID')
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
        """Return the name of the content provider as well as the content of the
        DOCNO tag that has that information."""
        content = self._get_tag_content('DOCNO')
        content = str(content)  # in case the above returned None
        for source_identifier in ('ABC', 'APW', 'AP', 'CNN', 'NYT', 'PRI',
                                  'SJMN', 'VOA', 'WSJ', 'ea', 'ed'):
            if content.startswith(source_identifier):
                return (source_identifier, content)
        logger.warn("Could not determine document source from DOCNO tag")
        return None

    def _parse_tag_content(self, regexpr, tagname):
        """Return the DCT part of the tag content of tagname, requires a reqular
        expression as one of the arguments."""
        content_string = self._get_tag_content(tagname)
        result = re.compile(regexpr).match(content_string)
        if result:
            (month, day, year) = result.groups()
            return "%s%s%s" % (year, month, day)
        else:
            logger.warn("Could not get date from %s tag" % tagname)
            return _get_today()


class MetadataParserATEE(MetadataParser):

    """The parser for ATEE document."""

    def get_dct(self):
        """All ATEE documents have a DATE tag with a value attribute, the value
        of that attribute is returned."""
        date_tag = self.tarsqidoc.sourcedoc.tags.find_tag('DATE')
        return date_tag.attrs['value']


class MetadataParserRTE3(MetadataParser):

    """The parser for RTE3 documents, no differences with the default parser."""


class MetadataParserDB(MetadataParser):

    """A minimal example parser for cases where the DCT is retrieved from a
    database. It is identical to MetadataParser except for how it gets the
    DCT. This is done by lookup in a database. This here is the simplest
    possible case, and it is quite inefficient. It assumes there is an sqlite
    database at 'TTK_ROOT/data/in/va/dct.sqlite' which was created as
    follows:

       $ sqlite3 dct.sqlite
       sqlite> create table dct (filename TEXT, dct TEXT)
       sqlite> insert into dct values ("test.xml", "1999-12-31");

    The get_dct() method uses this database and the location of the database is
    specified in the config.txt file. The first use case for this were VA
    documents where the DCT was stored externally. To see this in action run

       $ python tarsqi.py --source=db data/in/va/test.xml out.xml

    """

    def get_dct(self):
        fname = self._get_source().filename
        fname = os.path.basename(fname)
        db_location = self.options.getopt('dct-database')
        db_connection = sqlite3.connect(db_location)
        db_cursor = db_connection.cursor()
        db_cursor.execute('SELECT dct FROM dct WHERE filename=?', (fname,))
        dct = db_cursor.fetchone()[0]
        return dct


def _get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime())


def _get_dct_values(tag_repository):
    """Return the list of nromalized values from all TIMEX3 tags in the
    TagRepository."""
    timexes = [t for t in tag_repository.find_tags('TIMEX3')
               if t.attrs.get('functionInDocument') == 'CREATION_TIME']
    values = [t.attrs.get(LIBRARY.timeml.VALUE) for t in timexes]
    return values

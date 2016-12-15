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


class MetadataParser:

    """This is the minimal metadata parser that is used as a default. It sets the
    DCT to today's date and provides some common functionality to subclasses."""

    def __init__(self, options):
        """At the moment, initialization does not use any of the options,
        but this could change."""
        self.options = options
        self.tarsqidoc = None  # added in by the parse() method

    def parse(self, tarsqidoc):
        """Adds metadata to the TarsqiDocument. The only thing it adds to the
        metadata dictionary is the DCT, which is set to today."""
        self.tarsqidoc = tarsqidoc
        self.tarsqidoc.metadata['dct'] = self.get_dct()

    def get_dct(self):
        """Return today's date in YYYYMMDD format."""
        return get_today()

    def get_source(self):
        """A convenience method to lift the SourceDoc out of the tarsqi
        instance."""
        return self.tarsqidoc.sourcedoc

    def _get_tag_content(self, tagname):
        """Return the text content of the first tag with name tagname, return
        None if there is no such tag."""
        try:
            tag = self.get_source().tags.find_tags(tagname)[0]
            content = self.get_source().text[tag.begin:tag.end].strip()
            return content
        except IndexError:
            logger.warn("Cannot get the %s tag in this document" % tagname)
            return None


class MetadataParserTTK(MetadataParser):

    """The metadata parser for the ttk format, simply copies the meta data."""

    def parse(self, tarsqidoc):
        """Adds metadata to the TarsqiDocument. The only thing it adds to the
        metadata dictionary is the DCT, which is copied from the metadata in the
        SourceDoc."""
        self.tarsqidoc = tarsqidoc
        self.tarsqidoc.metadata['dct'] = self.get_dct(tarsqidoc.sourcedoc)

    def get_dct(self, sourcedoc):
        return sourcedoc.metadata.get('dct')


class MetadataParserText(MetadataParser):

    """For now this one adds nothing to the default metadata parser."""


class MetadataParserTimebank(MetadataParser):
    """The parser for Timebank documents. All it does is overwriting the
    get_dct() method."""

    def get_dct(self):
        """Extracts the document creation time, and returns it as a string of
        the form YYYYMMDD. Depending on the source, the DCT can be found in one
        of the following tags: DOCNO, DATE_TIME, PUBDATE or FILEID."""
        result = self._get_doc_source()
        if result is None:
            # dct defaults to today if we cannot find the DOCNO tag in the
            # document
            return get_today()
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
        """Return the name of the content provider as well as the content of the DOCNO
        tag that has that information."""
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
            return get_today()


class MetadataParserATEE(MetadataParser):

    """The parser for ATEE document."""

    def get_dct(self):
        """All ATEE documents have a DATE tag with a value attribute, the value
        of that attribute is returned."""
        date_tag = self.sourcedoc.tags.find_tag('DATE')
        return date_tag.attrs['value']


class MetadataParserRTE3(MetadataParser):

    """The parser for RTE3 documents, no differences with the default parser."""

    def get_dct(self):
        return get_today()


class MetadataParserDB(MetadataParser):

    """A minimal example parser for cases where the DCT is retrieved from a
    database. It is identical to MetadataParser except for how it gets the
    DCT. This is done by lookup in a database. This here is the simplest
    possible case, and it is quite inefficient. It assumes there is an sqlite
    database at 'TTK_ROOT/code/data/in/va/dct.sqlite' which was created as
    follows:

       $ sqlite3 dct.sqlite
       sqlite> create table dct (filename TEXT, dct TEXT)
       sqlite> insert into dct values ("test.xml", "1999-12-31");

    The get_dct() method uses this database and the location of the database is
    specified in the settings.txt file. The first use case for this were VA
    documents where the DCT was stored externally. To see this class in action
    run

       $ python tarsqi.py --source=va data/in/va/test.xml out.xml

    """

    def get_dct(self):
        fname = self.get_source().filename
        fname = os.path.basename(fname)
        db_location = self.options.getopt('dct-database')
        db_connection = sqlite3.connect(db_location)
        db_cursor = db_connection.cursor()
        db_cursor.execute('SELECT dct FROM dct WHERE filename=?', (fname,))
        dct = db_cursor.fetchone()[0]
        return dct


def get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime())

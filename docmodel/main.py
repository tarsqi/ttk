"""main.py

Initialization of parsers responsible for first-level processing.

This file includes the PARSERS dictionary (indexed on source identifiers, handed
in by the --source option). If a new source type is introduced, then an item
needs to be added to the PARSERS dictionary. In addition, if new parsers are
required they should be added to source_parser.py and metadata_parser.py.

"""

import os, xml

from docmodel.source_parser import SourceParserXML, SourceParserText
from docmodel.source_parser import SourceParserTTK
from docmodel.metadata_parser import MetadataParser, MetadataParserTTK
from docmodel.metadata_parser import MetadataParserText
from docmodel.metadata_parser import MetadataParserTimebank, MetadataParserDB
from docmodel.metadata_parser import MetadataParserATEE, MetadataParserRTE3
from docmodel.docstructure_parser import DocumentStructureParser

from utilities import logger


PARSERS = { 'ttk': (SourceParserTTK, MetadataParserTTK),
            'xml': (SourceParserXML, MetadataParser),
            'text': (SourceParserText, MetadataParserText),
            'timebank': (SourceParserXML, MetadataParserTimebank),
            'atee': (SourceParserXML, MetadataParserATEE),
            'rte3': (SourceParserXML, MetadataParserRTE3),
            'db': (SourceParserXML, MetadataParserDB) }


DEFAULT_SOURCE_PARSER = SourceParserXML
DEFAULT_METADATA_PARSER = MetadataParser


def create_source_parser(options):
    try:
        return PARSERS[options.source][0]()
    except KeyError:
        logger.warn("Unknown format, using default source parser")
        return DEFAULT_SOURCE_PARSER()


def create_metadata_parser(options):
    try:
        return PARSERS[options.source][1](options)
    except KeyError:
        logger.warn("Unknown format, using default metadata parser")
        return DEFAULT_METADATA_PARSER(options)


def create_docstructure_parser():
    """Return the default document structure parser."""
    # NOTE: this is just the default parser, no options needed
    # NOTE: it is also a stub, awaiting the full docstructure parser redesign
    return DocumentStructureParser()


def guess_source(filename_or_string):
    """Returns whether the source type of the content of the file or string is
    xml, ttk or text. This is a guess because the heuristics used are simple and
    just searching the first N characters of the input."""
    # this needs to be large enough so that you are very likely to at least
    # capture the first tag
    chars_to_read = 1000
    content = filename_or_string[:chars_to_read]
    if os.path.exists(filename_or_string):
        # using codecs.open gives unicode error
        fh = open(filename_or_string)
        content = fh.read(chars_to_read)
        fh.close()
    content = content.strip()
    first_tag = Xml(content).get_first_tag()
    if first_tag == 'ttk':
        return 'ttk'
    else:
        return 'text' if first_tag is None else 'xml'


class Xml(object):

    """Test class used for determining whether a string looks like it contains
    XML. Note that it does not do a full XML parse and that the string handed in
    is intended to be a prefix of the entire string or document that is being
    tested."""

    def __init__(self, content):
        self.parser = xml.parsers.expat.ParserCreate(encoding='utf-8')
        self.parser.StartElementHandler = self._handle_start
        self.content = content
        self.first_tag = None

    def _handle_start(self, name, attrs):
        if self.first_tag is None:
            self.first_tag = name

    def get_first_tag(self):
        """Returns the first XML tag of the content. The content does not have to
        be well-formed XML, as long as it starts with an optional XML declaration
        followed by a tag it will return the tag name of that tag. Returns None
        if there is no such tag."""
        try:
            self.parser.Parse(self.content)
        except xml.parsers.expat.ExpatError:
            pass
        return self.first_tag

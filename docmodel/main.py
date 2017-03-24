"""

Initialization of parsers responsible for first-level processing.

This file includes the PARSERS dictionary, which is indexed on a source
identifier (handed in by the --source option). If a new source type is
introduced, then an item needs to be added to the PARSERS dictionary. In
addition, if new parsers are required they should be added to source_parser.py
and metadata_parser.py.

"""

import os

from docmodel.source_parser import SourceParserXML, SourceParserText
from docmodel.source_parser import SourceParserTTK
from docmodel.metadata_parser import MetadataParser, MetadataParserTTK
from docmodel.metadata_parser import MetadataParserText
from docmodel.metadata_parser import MetadataParserTimebank, MetadataParserDB
from docmodel.metadata_parser import MetadataParserATEE, MetadataParserRTE3
from docmodel.docstructure_parser import DocumentStructureParser


PARSERS = {
    'ttk': (SourceParserTTK, MetadataParserTTK),
    'xml': (SourceParserXML, MetadataParser),
    'text': (SourceParserText, MetadataParserText),
    'timebank': (SourceParserXML, MetadataParserTimebank),
    'atee': (SourceParserXML, MetadataParserATEE),
    'rte3': (SourceParserXML, MetadataParserRTE3),
    'db': (SourceParserXML, MetadataParserDB)
}


DEFAULT_SOURCE_PARSER = SourceParserXML
DEFAULT_METADATA_PARSER = MetadataParser
DEFAULT_PARSERS = (DEFAULT_SOURCE_PARSER, DEFAULT_METADATA_PARSER)


def create_source_parser(options):
    source_parser, metadata_parser = PARSERS.get(options.source, DEFAULT_PARSERS)
    return source_parser()


def create_metadata_parser(options):
    source_parser, metadata_parser = PARSERS.get(options.source, DEFAULT_PARSERS)
    return metadata_parser(options)


def create_docstructure_parser():
    """Return the default document structure parser."""
    # NOTE. This is just the default parser, no options needed
    # TODO. It is also a stub, awaiting the full docstructure parser redesign,
    # where the parser creates tags similar to other components and where the
    # elements variable is gone.
    return DocumentStructureParser()

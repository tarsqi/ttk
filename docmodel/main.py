"""main.py

Initialization of parsers responsible for first-level processing.

This file includes the PARSERS dictionary (indexed on source identifiers, handed
in by the --source-format option). If a new source type is introduced, then an item
needs to be added to the PARSERS dictionary. In addition, if new parsers are
required they should be added to source_parser.py and metadata_parser.py.

"""

from __future__ import absolute_import
import os, re

from docmodel.source_parser import SourceParserXML, SourceParserText
from docmodel.source_parser import SourceParserTTK, SourceParserLIF
from docmodel.metadata_parser import MetadataParser, MetadataParserTTK
from docmodel.metadata_parser import MetadataParserText
from docmodel.metadata_parser import MetadataParserTimebank, MetadataParserDB
from docmodel.metadata_parser import MetadataParserATEE, MetadataParserRTE3
from docmodel.docstructure_parser import DocumentStructureParser

from utilities import logger
from io import open


PARSERS = {'ttk': (SourceParserTTK, MetadataParserTTK),
           'text': (SourceParserText, MetadataParserText),
           'lif': (SourceParserLIF, MetadataParser),
           'xml': (SourceParserXML, MetadataParser),
           'timebank': (SourceParserXML, MetadataParserTimebank),
           'atee': (SourceParserXML, MetadataParserATEE),
           'rte3': (SourceParserXML, MetadataParserRTE3),
           'db': (SourceParserXML, MetadataParserDB)}


DEFAULT_SOURCE_PARSER = SourceParserXML
DEFAULT_METADATA_PARSER = MetadataParser


def create_source_parser(options):
    try:
        return PARSERS[options.source_format][0]()
    except KeyError:
        logger.warn("Unknown format, using default source parser")
        return DEFAULT_SOURCE_PARSER()


def create_metadata_parser(options):
    try:
        return PARSERS[options.source_format][1](options)
    except KeyError:
        logger.warn("Unknown format, using default metadata parser")
        return DEFAULT_METADATA_PARSER(options)


def create_docstructure_parser():
    """Return the default document structure parser."""
    # NOTE: this is just the default parser, no options needed
    # NOTE: it is also a stub, awaiting the full docstructure parser redesign
    return DocumentStructureParser()

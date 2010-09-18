"""

Initialization of parsers responsible for document-level parsing.

This module is responsible for creating document source parsers. That is, parsers that
take an instance of DocSource and create an instance of Document (now still called
DocumentPlus to avoid confusion with the still existing class Document, which shall be
renamed into Text).

"""

import os

from utilities import logger
from docmodel.parsers import DefaultParser
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T
from library.tarsqi_constants import CLASSIFIER, BLINKER, LINK_MERGER, ARGLINKER


PARSERS = {
    'simple-xml': DefaultParser,
    'timebank': DefaultParser,
    'atee': DefaultParser,
    'rte3': DefaultParser }

DEFAULT_PIPELINE = [ PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T,
                     BLINKER, CLASSIFIER, LINK_MERGER ]



def create_parser(genre):

    """Return a document parser. Should include some additional setup of the parser, where
    depending on the genre and perhaps other future arguments some aspects of the parser
    class are set."""
    
    parser = PARSERS.get(genre, DefaultParser)
    return parser()


def get_default_pipeline(genre):

    """Now always returns the same but can be used for genre-specific pipelines."""
    
    return DEFAULT_PIPELINE



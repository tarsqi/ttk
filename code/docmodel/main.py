"""

Initialization of parsers responsible for document-level parsing.

"""

import os

from docmodel.parsers import SimpleParser, TimebankParser, ATEEParser, RTE3Parser, VAExampleParser
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T
from library.tarsqi_constants import CLASSIFIER, BLINKER, LINK_MERGER


PARSERS = {
    'simple-xml': SimpleParser,
    'timebank': TimebankParser,
    'atee': ATEEParser,
    'rte3': RTE3Parser,
    'va': VAExampleParser }

DEFAULT_PIPELINE = [ PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T,
                     BLINKER, CLASSIFIER, LINK_MERGER ]


def create_parser(source, parameters):
    """Return a document parser. Should include some additional setup of the parser,
    where depending on the genre and perhaps other future arguments some aspects
    of the parser class are set."""
    parser = PARSERS.get(source, SimpleParser)
    return parser(parameters)

def get_default_pipeline(genre):
    """Now always returns the same but can be used for genre-specific pipelines."""
    return DEFAULT_PIPELINE



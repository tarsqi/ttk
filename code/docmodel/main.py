"""Initialization of parsers responsible for document-level parsing.

This module is responsible for creating document source parsers. That is,
parsers that take an instance of SourceDoc and create an instance of
TarsqiDocument.

"""

# TODO: consider moving this code to parsers.py

import os

from docmodel.parsers import DefaultParser, TimebankParser, ATEEParser, RTE3Parser
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T
from library.tarsqi_constants import CLASSIFIER, BLINKER, LINK_MERGER, ARGLINKER


PARSERS = {
    'simple-xml': DefaultParser,
    'timebank': TimebankParser,
    'atee': ATEEParser,
    'rte3': RTE3Parser }

DEFAULT_PIPELINE = [ PREPROCESSOR, GUTIME, EVITA, SLINKET, S2T,
                     BLINKER, CLASSIFIER, LINK_MERGER ]


def create_parser(genre, parameters):
    """Return a document parser. Should include some additional setup of the parser,
    where depending on the genre and perhaps other future arguments some aspects
    of the parser class are set."""
    parser = PARSERS.get(genre, DefaultParser)
    return parser(parameters)

def get_default_pipeline(genre):
    """Now always returns the same but can be used for genre-specific pipelines."""
    return DEFAULT_PIPELINE



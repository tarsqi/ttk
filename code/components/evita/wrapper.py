"""

Contains the Evita wrapper.

"""

from library.tarsqi_constants import EVITA
from components.evita.main import Evita
from utilities import logger


class EvitaWrapper:
    """Wrapper for Evita. """

    def __init__(self, document):
        """Sets instance variables."""
        self.component_name = EVITA
        self.document = document
        
    def process(self):
        """Hand in all document elements to Evita for processing. Document
        elements are instances of docmodel.document.TarsqiDocParagraph (a
        subclass of docmodel.document.TarsqiDocElement). This is a simple
        approach that assumes that all document elements are processed the same
        way."""
        for element in self.document.elements:
            Evita().process_element(element)

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
        """Retrieve the xmldoc and hand it to Evita for processing. Evita processing will
        update the xmldoc when events are added. No arguments and no return value."""
        for element in self.document.elements:
            # element is an instance of docmodel.document.TarsqiDocParagraph (which is a
            # subclass of docmodel.document.TarsqiDocElement)
            Evita().process_element(element)

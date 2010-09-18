"""

Contains the Evita wrapper.

"""

from time import time
from library.tarsqi_constants import EVITA
from components.evita.main import Evita
from utilities import logger


class EvitaWrapper:

    """Wrapper for Evita. """
    

    def __init__(self, document, tarsqi_instance):

        """Sets instance variables."""

        self.component_name = EVITA
        self.document = document
        
        
    def process(self):

        """Retrieve the xmldoc and hand it to Evita for processing. Evita processing will update
        the xmldoc when events are added. No arguments and no return value."""

        begin_time = time()
        xmldocs = [self.document.xmldoc]
        for xmldoc in xmldocs:
            xmldoc.reset()
            Evita().process_xmldoc(xmldoc)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

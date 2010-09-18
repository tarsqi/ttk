"""

Contains the Blinker wrapper.

"""

from time import time
from library.tarsqi_constants import BLINKER
from components.blinker.main import Blinker
from utilities import logger


class BlinkerWrapper:

    """Wrapper for Blinker."""

    
    def __init__(self, document, tarsqi_instance):

        self.component_name = BLINKER
        self.document = document
        self.dct = self.document.get_dct()

        
    def process(self):

        """Retrieve the XmlDocument and hand it to Evita for processing. Blinker processing will
        update this slice when events are added."""

        begin_time = time()
        xmldocs = [self.document.xmldoc]
        for xmldoc in xmldocs:
            xmldoc.reset()
            Blinker().process_xmldoc(xmldoc, self.dct)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

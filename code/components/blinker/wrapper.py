"""

Contains the Blinker wrapper.

"""

from library.tarsqi_constants import BLINKER
from components.blinker.main import Blinker


class BlinkerWrapper:
    """Wrapper for Blinker."""
    
    def __init__(self, document):
        self.component_name = BLINKER
        self.document = document
        self.dct = self.document.get_dct()
        
    def process(self):
        """Retrieve the XmlDocument and hand it to Evita for processing. Blinker
        processing will update this slice when events are added."""
        xmldocs = [self.document.xmldoc]
        for xmldoc in xmldocs:
            xmldoc.reset()
            Blinker().process_xmldoc(xmldoc, self.dct)

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
        """Hand in all document elements to Blinker for processing. Document elements are
        instances of docmodel.document.TarsqiDocParagraph (which is a subclass
        of TarsqiDocElement). Assumes that all
        document elements are processed the same way."""
        for element in self.document.elements:
            Blinker(self.document).process_element(element, self.dct)

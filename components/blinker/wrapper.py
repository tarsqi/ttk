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

    def process(self):
        """Hand in all document elements to Blinker for processing. Document
        elements are instances of Tag with name=docelement."""
        blinker = Blinker(self.document)
        blinker.run_timex_linking()
        for element in self.document.elements():
            blinker.process_element(element)

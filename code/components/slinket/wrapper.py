"""

Contains the Slinket wrapper.

"""

from library.tarsqi_constants import SLINKET
from components.slinket.main import Slinket
from components.common_modules import tree
from utilities import logger


class SlinketWrapper:
    """Wrapper for Slinket."""

    def __init__(self, tarsqi_document):
        self.component_name = SLINKET
        self.document = tarsqi_document

    def process(self):
        """Create a TarsqiTree instance for each docelement slice of the TarsqiDocument
        and hand them to Slinket for processing. Slinket processing will update
        the tags in the TarsqiDocument when slinks are added."""
        self.document.tags.index_events()
        self.document.tags.index_timexes()
        for element in self.document.elements():
            doctree = tree.create_tarsqi_tree(self.document, element)
            Slinket().process_doctree(doctree)

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
        """Create a TarsqiTree instance for each TarsqiDocElement hand them to Slinket
        for processing. Slinket processing will update the tags in the
        TarsqiDocElement when slinks are added."""
        for element in self.document.elements:
            # print '>>>>>', element
            doctree = tree.create_tarsqi_tree(element)
            Slinket().process_doctree(doctree)

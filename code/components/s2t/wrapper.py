"""

Contains the S2tWrapper.

"""

from library.tarsqi_constants import S2T
from components.s2t.main import Slink2Tlink
from components.common_modules import tree


class S2tWrapper:

    """Wraps the S2T components."""

    def __init__(self, document):

        self.component_name = S2T
        self.document = document

    def process(self):
        """Try to add TLINKS for all the SLINKS in each TarsqiDocElement."""
        for element in self.document.elements:
            # print '>>>>>', element
            doctree = tree.create_tarsqi_tree(element)
            Slink2Tlink().process_doctree(doctree)

"""

Contains the S2tWrapper.

"""

from library.tarsqi_constants import S2T
from components.s2t.main import Slink2Tlink
from components.common_modules import tree


class S2tWrapper:

    """Wraps the S2T component."""

    def __init__(self, document):
        self.component_name = S2T
        self.document = document

    def process(self):
        """Try to add TLINKS for all the SLINKS in each element."""
        # NOTE: it is a bit weird that this has to be done here and on Slinket,
        # the thing is that this is not done when the TarsqiDocument and its
        # repository is first created (in which case there usually aren't any
        # times and events), so we do it for those components that need it,
        # without relying on it having been done before.
        self.document.tags.index_events()
        self.document.tags.index_timexes()
        for element in self.document.elements():
            doctree = tree.create_tarsqi_tree(self.document, element, links=True)
            Slink2Tlink().process_doctree(doctree)

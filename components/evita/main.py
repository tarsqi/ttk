"""Main module for Evita, the event recognition component.

Responsible for the top-level processing of Evita.

"""

from components.common_modules.utils import get_words_as_string
from components.common_modules.component import TarsqiComponent
from components.common_modules.tree import create_tarsqi_tree
from library.tarsqi_constants import EVITA
from utilities import logger


class Evita (TarsqiComponent):

    """Class that implements Evita's event recognizer. Instance variables contain
    the name of the component, the TarsqiDocument, a docelement Tag and a
    TarsqiTree instance. The TarsqiTree instance in the doctree variable is the
    tree for just one element and not for the whole document or string."""

    def __init__(self, tarsqidoc, docelement, imported_events):
        """Set the NAME instance variable. The doctree variables is filled in
        during processing."""
        self.NAME = EVITA
        self.tarsqidoc = tarsqidoc              # instance of TarsqiDocument
        self.docelement = docelement            # instance of Tag
        self.doctree = None                     # instance of TarsqiTree
        self.imported_events = imported_events  # dict of int=>Tag

    def process_element(self):
        """Process the element slice of the TarsqiDocument. Loop through all
        sentences in self.doctree and through all nodes in each sentence and
        determine if the node contains an event. Events are added to the tag
        repository on the element."""
        self.doctree = create_tarsqi_tree(self.tarsqidoc, self.docelement)
        for sentence in self.doctree:
            # print get_words_as_string(sentence)
            logger.debug("SENTENCE: %s" % get_words_as_string(sentence))
            for node in sentence:
                if node.isEvent():
                    continue
                if not node.checkedEvents:
                    node.createEvent(imported_events=self.imported_events)

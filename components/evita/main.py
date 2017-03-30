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

    def __init__(self, tarsqidoc, docelement):
        """Set the NAME instance variable. The doctree variables is filled in during
        processing."""
        self.NAME = EVITA
        self.tarsqidoc = tarsqidoc    # instance of TarsqiDocument
        self.docelement = docelement  # instance of Tag
        self.doctree = None           # will be an instance of TarsqiTree

    def process_element(self):
        """Process the element slice of the TarsqiDocument. Loop through all
        sentences in self.doctree and through all nodes in each sentence and
        determine if the node contains an event. Events are added to the tag
        repository on the element."""
        self.doctree = create_tarsqi_tree(self.tarsqidoc, self.docelement)
        imported_events = self.import_events()
        for sentence in self.doctree:
            # print get_words_as_string(sentence)
            logger.debug("SENTENCE: %s" % get_words_as_string(sentence))
            for node in sentence:
                if node.isEvent():
                    continue
                if not node.checkedEvents:
                    node.createEvent(imported_events=imported_events)

    def import_events(self):
        """Returns a dictionary of events. The dictionary is indexed on character
        offsets where a character occurs in the keys if it is included in the
        span of an event. This is to import events from tags that were available
        in the source_tags repository prior to the TTK pipeline application."""
        imported_events = {}
        event_tag = self.tarsqidoc.options.import_event_tags
        if event_tag is not None:
            tags = self.tarsqidoc.sourcedoc.tags.find_tags(event_tag)
            for tag in tags:
                # Use character offsets of all characters in the event, so if we
                # have "He sleeps." with sleep from 3 to 9, then the offsets are
                # [3,4,5,6,7,8] since offset 9 points to the period.
                offsets = range(tag.begin, tag.end)
                for off in offsets:
                    if imported_events.has_key(off):
                        logger.warning("Overlapping imported events")
                    imported_events[off] = tag
        return imported_events

"""

Contains the Evita wrapper.

"""

from library.tarsqi_constants import EVITA
from library.main import LIBRARY
from components.evita.main import Evita


# Set this to True if you want to do a simplistic evaluation of how many of the
# events that should be imported actually are imported.
EVALUATE_EVENT_IMPORT = False


EVENT = LIBRARY.timeml.EVENT


class EvitaWrapper:

    """Wrapper for Evita."""

    def __init__(self, document):
        """Sets instance variables."""
        self.component_name = EVITA
        self.document = document
        
    def process(self):
        """Hand in all document elements to Evita for processing. Document
        elements are instances of Tag with name=docelement. This is a simple
        approach that assumes that all document elements are processed the same
        way."""
        imported_events = self._import_events()
        for element in self.document.elements():
            Evita(self.document, element, imported_events).process_element()
        if self.document.options.import_events and EVALUATE_EVENT_IMPORT:
            self._evaluate_results(imported_events)

    def _import_events(self):
        """Returns a dictionary of events. The dictionary is indexed on character
        offsets where a character occurs in the keys if it is included in the
        span of an event. This is to import events from tags that were available
        in the source_tags repository prior to the TTK pipeline application."""
        imported_events = {}
        if self.document.options.import_events:
            events = self.document.sourcedoc.tags.find_tags(EVENT)
            for event in events:
                # Use character offsets of all characters in the event, so if we
                # have "He sleeps." with sleep from 3 to 9, then the offsets are
                # [3,4,5,6,7,8] since offset 9 points to the period.
                offsets = range(event.begin, event.end)
                for off in offsets:
                    if imported_events.has_key(off):
                        logger.warning("Overlapping imported events")
                    imported_events[off] = event
        return imported_events

    def _evaluate_results(self, imported_events):
        """Simplistic evaluation of how many of the imported events actually end
        up as events. Loops through all the events that should be imported and
        checks whether one of its offsets is actually part of a event found by
        the system."""
        events_key = self.document.sourcedoc.tags.find_tags(EVENT)
        if not events_key:
            print  "Nothing to evaluate"
        else:
            events_system = {}
            for e in self.document.tags.find_tags(EVENT):
                for i in range(e.begin, e.end):
                    events_system[i] = True
            imported = 0
            for e in events_key:
                for i in range(e.begin, e.end):
                    if i in events_system:
                        imported += 1
                        break
            percentage = imported * 100 / len(events_key)
            print "\n\nEVENTS TO BE IMPORTED:  %3s" % len(events_key)
            print "FOUND BY SYSTEM:        %3s (%s%%)\n" % (imported, percentage)


def _pp_imported_events(imported_events):
    fh = open("tmp-imported-events.txt", 'w')
    fh.write("LENGTH: %s\n\n" % len(imported_events))
    for offset in sorted(imported_events.keys()):
        fh.write("%s %s-%s\n" % (offset,
                                 imported_events[offset].begin,
                                 imported_events[offset].end))

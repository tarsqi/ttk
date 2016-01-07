"""Contains functionality specific to sentences in a tree."""

from utilities import logger
from components.common_modules.constituent import Constituent


class Sentence(Constituent):

    """A Sentence is a top-level element of a TarsqiTree. It contains a list of
    Chunks and Tokens.
    
    Instance variables
        dtrs - a list of Chunks and Tokens
        eventList - a list of (eLoc, eid) tuples
        position - position in the TarsqiTree parent (first sentence is 0)
        parent - a TarsqiTree

    The eventList variable stores (eLoc, eid) tuples of each tagged event in the sentence,
    the eLoc is the location of the event inside the embedding constituent, usually a
    chunk).

    """

    def __init__(self):
        """Initialize all instance variables to 0, None or the empty list."""
        self.parent = None
        self.dtrs = []
        self.eventList = [] 
        self.position = None
        self.parent = None
        
    def __len__(self):
        """Returns length of dtrs variable."""
        return len(self.dtrs)

    def __getattr__(self, name):
        """This is here so that an unknown attribute is not dealt with by
        __getattr__ on Constituent, with possibly unwelcome results."""
        raise AttributeError, name

    def add(self, chunkOrToken):
        """Add a chunk or token to the end of the sentence. Sets the sentence as the value
        of the parents variable on the chunk or token.
        Arguments
           chunkOrToken - a Chunk or a Token"""
        chunkOrToken.setParent(self)
        self.dtrs.append(chunkOrToken)

    def storeEventLocation(self, evLoc, eid):
        """Appends a tuple of event location (an integer) and event id to the eventList."""
        self.eventList.append((evLoc, eid))

    def get_event_list(self):
        """Return the list of eLocation-eid tuples of the sentence."""
        event_list = []
        eventLocation = -1
        for element in self:
            eventLocation += 1
            if element.isChunk():
                event = element.embedded_event()
                if event:
                    event_list.append((eventLocation, event.eid))
            elif element.isToken() and element.event:
                event_list.append((eventLocation, element.eid))
        return event_list

    def set_event_list(self):
        """Set the value of self.eventList to the list of eLocation-eid tuples
        in the sentence. This is used by Slinket."""
        self.eventList = self.get_event_list()

    def pretty_print(self, tree=True, verbose=False):
        """Pretty print the sentence by pretty printing all daughters"""
        if verbose:
            print "SENTENCE %s\n" % self.position
            print "  parent     =  %s" % self.parent
            print "  eventList  =  %s\n" % self.eventList
        else:
            print "<Sentence position=%s>" % self.position
        if tree or verbose:
            for dtr in self.dtrs:
                dtr.pretty_print(indent=2)

    def pp(self, tree=True):
        """Delegates to self.pretty_print()."""
        self.pretty_print(tree)

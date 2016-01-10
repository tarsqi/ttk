"""Contains functionality specific to sentences in a tree."""

from utilities import logger
from components.common_modules.constituent import Constituent


class Sentence(Constituent):

    """A Sentence is a top-level element of a TarsqiTree. It contains a list of
    Chunks and Tokens.
    
    Instance variables
        parent     -  a TarsqiTree
        dtrs       -  a list of Chunks and Tokens
        position   -  position in the TarsqiTree parent (first sentence is 0)
        eventList  -  a list of (eLoc, eid) tuples

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

    def set_event_list(self):
        """Set the value of self.eventList to the list of eLocation-eid tuples
        in the sentence. This is used by Slinket."""
        self.eventList = []
        eventLocation = -1
        for element in self:
            eventLocation += 1
            if element.isChunk():
                event = element.embedded_event()
                # NOTE: this used to be "if event:", but the combination of that
                # with EventTag.__getattr__ caused errors apparently because
                # __nonzero__ was intercepted by __getattr__
                if event is not None:
                    self.eventList.append((eventLocation, event.eid))
            elif element.isToken() and element.event:
                self.eventList.append((eventLocation, element.eid))

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

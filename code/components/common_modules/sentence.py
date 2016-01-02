"""Contains functionality specific to sentences in a document."""

from utilities import logger


class Sentence:

    """A Sentence is a top-level element of a Document. It contains a list of Chunks and
    Tokens.
    
    Instance variables
        dtrs - a list of Chunks and Tokens
        chunkIndex - an integer
        eventList - a list of (eLoc, eid) tuples
        position - position in the Document parent (first sentence is 0)
        positionCount - used when looping through the daughters
        parent - a Document

    The eventList variable stores (eLoc, eid) tuples of each tagged event in the sentence,
    the eLoc is the location of the event inside the embedding constituent, usually a
    chunk)."""

    def __init__(self):
        """Initialize all instance variables to 0, None or the empty list."""
        self.dtrs = []
        self.chunkIndex = 0
        self.eventList = [] 
        self.position = None
        self.positionCount = 0
        self.parent = None
        
    def __len__(self):
        """Returns length of dtrs variable."""
        return len(self.dtrs)

    def __getitem__(self, index):
        """Get an item from the dtrs variable."""
        if index is None:
            logger.warn("Given index to __getitem__ in Sentence is None")
            return None
        return self.dtrs[index]

    def __setitem__(self, idx, element):
        """Set an element in the dtrs variable. In practice, idx is a slice and element
        a list."""
        self.dtrs[idx] = element

    def isAdjToken(self):
        # TODO: this is really a nasty hack and Sentence should be a sub class
        # of Constituent, but I do not want to do that till I have sorted out
        # the __getattr__ stuff.
        return False

    def isEvent(self):
        # TODO: see the note on isAdjToken()
        return False

    def get_events(self, result=None):
        # TODO: see the note on isAdjToken()
        if result is None:
            result = []
        for dtr in self.dtrs:
            if dtr.isEvent():
                result.append(dtr)
            dtr.get_events(result)
        return result

    def document(self):
        """Return the document that the sentence is in."""
        return self.parent.document()

    def add(self, chunkOrToken):
        """Add a chunk or token to the end of the sentence. Sets the sentence as the value
        of the parents variable on the chunk or token.
        Arguments
           chunkOrToken - a Chunk or a Token"""
        chunkOrToken.setParent(self)
        self.dtrs.append(chunkOrToken)
        self.positionCount += 1

    def setParent(self, parent):
        """Set the parent feature of the sentence to the document. Also copies the
        postionCount variable of the parent to the position variable of the sentence.
        Arguments
           parent - a Document"""
        self.parent = parent
        self.position = parent.positionCount

    def storeEventLocation(self, evLoc, eid):
        """Appends a tuple of event location and event id to the eventList.
        Arguments
           evLoc - an integer
           eid - an eid"""
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

    def getTokens(self):
        """Return the list of tokens in a sentence."""
        # NOTE: seems to be used by the evita NominalTrainer only
        # TODO: does not deal with event and timex3 tags
        tokenList = []
        for dtr in self.dtrs:
            if dtr.isToken():
                tokenList.append(dtr)
            elif dtr.isChunk():
                tokenList += dtr.dtrs
            else:
                logger.warn("Sentence element that is not a chunk or token")
        return tokenList

    def pretty_print(self, tree=True):
        """Pretty print the sentence by pretty printing all daughters"""
        print "  parent        = %s" % self.parent
        print "  chunkIndex    = %s" % self.chunkIndex
        print "  position      = %s" % self.position
        print "  eventList     = %s" % self.eventList
        if tree:
            print
            for dtr in self.dtrs:
                dtr.pretty_print(indent=2)

    def pp(self, tree=True):
        """Delegates to self.pretty_print()."""
        self.pretty_print(tree)

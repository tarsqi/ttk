"""NOT YET PROPERLY DOCUMENTED"""

from library import forms
from library.timeMLspec import FORM, STEM, POS, TENSE, ASPECT
from library.timeMLspec import EPOS, POS_PREP, MOD, POL, EVENTID, EIID, CLASS
from utilities import logger
from components.evita.event import Event
from components.evita.gramChunk import GramNChunk, GramAChunk, GramVChunkList
from components.common_modules.constituent import Constituent


class Token(Constituent):

    def __init__(self, document, pos, lid=0, lex=None):
        """Initialize with Document instance, a part-of-speech, an identifier
        and an instance of XmlDocElement with tag=lex (which came from the
        FragmentConverter). Some instance variables will be filled in later,
        depending on what the Token is used for."""
        self.pos = pos
        self.lid = lid
        self.lex = lex
        self.dtrs = []
        self.begin = None
        self.end = None
        self.event = None
        self.textIdx = None
        self.document = document
        self.position = None       # does not appear to be used on Token
        self.parent = None
        self.gramchunk = None
        self.checkedEvents = False
        self.text = None
        # added this one to provide a pointer to the XmlDocElement instance. Made it into
        # a list of all the docelements BK 20080725
        self.lex_tag_list = []

    def __getitem__(self, index):
        if index == 0:
            return self
        else:
            raise IndexError("list index out of range")

    def __len__(self):
        return 1

    def __getattr__(self, name):
        """Used by Sentence._match. Needs cases for all instance
        variables used in the pattern matching phase."""
        if name == 'nodeType':
            return self.__class__.__name__
        elif name == 'text':
            return self.getText()
        elif name == 'pos':
            return self.pos
        elif name in ['eventStatus', FORM, STEM, TENSE, ASPECT,
                      EPOS, MOD, POL, EVENTID, EIID, CLASS]:
            return None
        else:
            raise AttributeError, name

    def setTextNode(self, docLoc):
        """An essential step taken by the converter to fill in the textIdx, which the
        initialization method on Token had not done."""
        self.textIdx = docLoc

    def getText(self):
        """Return the text of the token, taking it from the node list on the
        document if it is not available on the text instance variable."""
        if self.text is None:
            self.text = self.document.nodeList[self.textIdx]
        return self.text

    def document(self):
        """Tokens have a document variable. Use this variable and avoid looking all the
        way up the tree."""
        return self.document

    def isToken(self):
        """Returns True"""
        return True

    def isMainVerb(self):
        """Return True if self is a main verb and False if not."""
        return self.pos[0] == 'V' and self.getText() not in forms.auxVerbs

    def isPreposition(self):
        """Return True if self is a preposition and False if not."""
        # TODO: note that this returns False if self is 'to' as in 'to the barn'
        return self.pos == POS_PREP

    def createEvent(self, tarsqidoc):
        """Do nothing when an AdjectiveToken or Token is asked to create an
        event. Potential adjectival events are processed from the VerbChunk
        using the createAdjEvent() method. Do not log a warning since it is
        normal for a Token to be asked this. Note that this method exists
        because a warning is logged on createEvent() on Constituent."""
        pass

    def debug_string(self):
        return "<%s: %s %s event=%s>" % \
            (self.__class__.__name__, self.getText(), self.pos, self.event)

    def pp(self):
        self.pretty_print()

    def pretty_print(self, indent=0):
        event_string = ''
        if self.event:
            eid = self.event_tag.attrs.get('eid')
            eiid = self.event_tag.attrs.get('eiid')
            event_string = " eid=%s eiid=%s" % (eid, eiid)
        print "%s<%s lid=%s pos=%s text=%s%s>" % \
            (indent * ' ', self.__class__.__name__,
             self.lid, self.pos, self.getText(), event_string)


class AdjectiveToken(Token):

    def __init__(self, document, pos, lid=0, lex=None):
        Token.__init__(self, document, pos, lid, lex)
        self.event = None      # set to True if self is wrapped in an EventTag
        self.eid = None        # the eid of the EventTag
        self.event_tag = None  # contains the EventTag

    def __getattr__(self, name):
        """(Slinket method) Used by Sentence._match. Needs cases for all instance
        variables used in the pattern matching phase."""

        if name == 'nodeType':
            return self.__class__.__name__
        if name == 'text':
            return self.getText()
        if name == 'pos':
            return self.pos
        if name == 'nodeName':
            return self.pos

        # this is used by slinket/s2t in case the adjective is an event
        if name in ['eventStatus', 'text', FORM, STEM, POS, TENSE, ASPECT,
                    EPOS, MOD, POL, EVENTID, EIID, CLASS]:
            if not self.event:
                return None
            doc = self.parent.document()
            if name == 'eventStatus':
                return '1'
            if name == 'text' or name == FORM:
                return doc.taggedEventsDict[self.eid][FORM] 
            if name == MOD:
                return doc.taggedEventsDict[self.eid].get(MOD,'NONE')
            if name == POL:
                return doc.taggedEventsDict[self.eid].get(POL,'POS')
            if name == POS:
                return doc.taggedEventsDict[self.eid].get(POS,'NONE')
            return doc.taggedEventsDict[self.eid][name]
        else:
            raise AttributeError, name

        
    def createAdjEvent(self, verbGramFeats=None, tarsqidoc=None):
        """Processes the adjective after a copular verb and make it an event if the
        adjective has an event class."""
        logger.debug("AdjectiveToken.createAdjEvent(verbGramFeat=%s)" % verbGramFeats)
        if not self.parent.__class__.__name__ == 'Sentence':
            logger.warn("Unexpected syntax tree")
            return
        self.gramchunk = GramAChunk(self, verbGramFeats)
        logger.debug(self.gramchunk.as_verbose_string())
        self._processEventInToken()

    def _processEventInToken(self):
        """Check whether there is an event class and add the event to self.document if
        there is one. There is a sister of this method on Chunk."""
        if self.gramchunk.evClass:
            self.document.addEvent(Event(self.gramchunk))

    def isAdjToken(self):
        return True

    def doc(self):
        return self.parent.document()

    def setEventInfo(self, eid):
        self.event = 1
        self.eid = eid

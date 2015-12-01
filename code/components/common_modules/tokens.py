"""NOT YET PROPERLY DOCUMENTED"""

from library import forms
from library.timeMLspec import FORM, STEM, POS, TENSE, ASPECT
from library.timeMLspec import EPOS, MOD, POL, EVENTID, EIID, CLASS
from utilities import logger
from components.evita.event import Event
from components.evita.gramChunk import GramNChunk, GramAChunk, GramVChunkList
from components.common_modules.constituent import Constituent


class Token(Constituent):

    def __init__(self, document, pos, lid=0, lex=None):
        self.pos = pos
        self.lid = lid
        self.lex = lex   # an XMLDocElement with tag=lex, from the FragmentConverter
        self.event = None
        self.textIdx = []          # should be None?
        self.document = document
        self.position = None
        self.parent = None
        self.gramchunk = None
        self.checkedEvents = False
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
        self.textIdx = docLoc

    def getText(self):
        return self.document.nodeList[self.textIdx]

    def document(self):
        """For some reason, tokens have a document variable. Use this variable and avoid
        looking all the way up the tree"""
        return self.document

    def isToken(self):
        return 1

    def isPreposition(self):
        """Perhaps needs a non-hard-coded value."""
        return self.pos == 'IN'
    
    def createEvent(self, tarsqidoc):
        """Do nothing when an AdjectiveToken or Token is asked to create an event.
        Potential adjectival events are processed from the VerbChunk using the
        createAdjEvent() method. Do not log a warning since it is normal for a
        Token to be asked this. Note that a warning is logged on createEvent()
        on Constituent."""
        pass

    def debug_string(self):
        try:
            event_val = self.event
        except AttributeError:
            event_val = None
        return "%s: %s %s Event:%s" % \
               (self.__class__.__name__, self.getText(), self.pos, str(event_val))

    def pp(self):
        self.pretty_print()

    def pretty_print(self, indent=0):
        event_string = ''
        if self.event:
            event_string = ' event="' + str(self.event_tag.attrs) + '"'
        print "%s<%s lid=\"%s\" pos=\"%s\" text=\"%s\"%s>" % \
            (indent * ' ', self.__class__.__name__,
             self.lid, self.pos, self.getText(), event_string)


class NewToken(Token):
    """Playpen to put in some functionality that should replace what is in Token."""

    def __init__(self, document, id, text, pos, stem, begin, end):

        self.document = document
        self.text = text
        self.pos = pos
        self.lid = id

        self.event = None
        self.textIdx = []          # should be None? -> probably not, it is a slice
        self.position = None
        self.parent = None
        self.cachedGramChunk = 0
        self.checkedEvents = False
        # added this one to provide a pointer to the XmlDocElement instance.  Made it into
        # a list of all the docelements BK 20080725
        self.lex_tag_list = []

    def getText(self):
        return self.text


class AdjectiveToken(Token):

    def __init__(self, document, pos, lid=0, lex=None):
        Token.__init__(self, document, pos, lid, lex)
        self.event = None
        self.eid = None

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

        
    def createAdjEvent(self, verbGramFeat=None, tarsqidoc=None):
        """Processes the adjective after a copular verb and make it an event if some
        conditions are met. The conditions are that the adjective needs to have
        a head and an event class."""
        logger.debug("AdjectiveToken.createAdjEvent(verbGramFeat=%s)" % verbGramFeat)
        if not self.parent.__class__.__name__ == 'Sentence':
            logger.warn("Unexpected syntax tree")
            return
        self.gramchunk = GramAChunk(self)
        # percolating grammatical features from the copular verb
        self.gramchunk.add_verb_features(verbGramFeat)
        logger.debug(self.gramchunk.as_extended_string())
        self._processEventInToken()

    def _processEventInToken(self):
        """Perform a few little checks on the head and check whether there is an event
        class, then add the event to self.document. This method is similar to
        Chunk._processEventInChunk()."""
        # TODO: the second test seems useless given that this is an adjective,
        # why is it there?
        if (self.gramchunk.head
            and self.gramchunk.head.getText() not in forms.be
            and self.gramchunk.evClass):
            self.document.addEvent(Event(self.gramchunk))

    def isAdjToken(self):
        return 1

    def doc(self):
        return self.parent.document()

    def setEventInfo(self, eid):
        self.event = 1
        self.eid = eid

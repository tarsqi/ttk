"""NOT YET PROPERLY DOCUMENTED"""

from library import forms
from library.timeMLspec import FORM, STEM, POS, TENSE, ASPECT
from library.timeMLspec import EPOS, MOD, POL, EVENTID, EIID, CLASS
from utilities import logger
from components.evita.event import Event
from components.evita.gramChunk import GramNChunk, GramAChunk, GramVChunkList
from components.common_modules.constituent import Constituent


class Token(Constituent):

    def __init__(self, document, pos, lid=0):
        self.pos = pos
        self.lid = lid
        self.event = None
        self.textIdx = []          # should be None?
        self.document = document
        self.position = None
        self.parent = None
        self.cachedGramChunk = 0
        self.flagCheckedForEvents = 0
        # added this one to provide a pointer to the XmlDocElement instance.  Made it into
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

    def _processEventInToken(self, gramChunk):
        doc = self.document
        if (gramChunk.head and
            gramChunk.head.getText() not in forms.be and
            gramChunk.evClass):
            doc.addEvent(Event(gramChunk))

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
    
    def createEvent(self):
        pass

    def debug_string(self):
        try:
            event_val = self.event
        except AttributeError:
            event_val = None
        return "%s: %s %s Event:%s" % \
               (self.__class__.__name__, self.getText(), self.pos, str(event_val))

    def pretty_print(self, indent=0):
        event_string = ''
        if self.event:
            event_string = ' event="' + str(self.event_tag.attrs) + '"'
            
        print "%s<lex lid=\"%s\" pos=\"%s\" text=\"%s\"%s>" % \
              (indent * ' ', self.lid, self.pos, self.getText(), event_string)


class NewToken(Token):
    """Playpen to put in some functionality that should replace what is in Token."""

    def __init__(self, document, id, text, pos, stem, begin, end):

        self.document = document
        self.text = text
        self.pos = pos
        self.lid = id

        self.event = None
        self.textIdx = []          # should be None?
        self.position = None
        self.parent = None
        self.cachedGramChunk = 0
        self.flagCheckedForEvents = 0
        # added this one to provide a pointer to the XmlDocElement instance.  Made it into
        # a list of all the docelements BK 20080725
        self.lex_tag_list = []

    def getText(self):
        return self.text


        
class AdjectiveToken(Token):

    def __init__(self, document, pos, lid=0):
        Token.__init__(self, document, pos, lid)
        self.event = None
        self.eid = None
        
    def _createGramChunk(self):
        self.cachedGramChunk = GramAChunk(self)


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

        
    def createEvent(self):
        """Arriving here adjs passed through the main loop for createEvent"""
        logger.debug("createEvent in AdjToken")
        pass
    
    def createAdjEvent(self, verbGramFeat='nil'):
        """(Evita method) only for tokens that are not in a chunk"""
        logger.debug("createAdjEvent in AdjToken")
        if not self.parent.__class__.__name__ == 'Sentence':
            return
        else:
            GramACh = self.gramChunk()
            if verbGramFeat !='nil':
                """ Percolating gram features from copular verb"""
                GramACh.tense = verbGramFeat['tense']
                GramACh.aspect = verbGramFeat['aspect']
                GramACh.modality = verbGramFeat['modality']
                GramACh.polarity = verbGramFeat['polarity']
                logger.debug("Accepted Adjective")
                logger.debug("[A_APC] " + GramACh.as_extended_string())
            else: 
                logger.debug("[A_2Ev] " + GramACh.as_extended_string())
            self._processEventInToken(GramACh)            

    def isAdjToken(self):
        return 1

    def doc(self):
        return self.parent.document()

    def setEventInfo(self, eid):
        self.event = 1
        self.eid = eid


from library import forms
from library.main import LIBRARY
from components.evita.event import Event
from components.evita.features import AChunkFeatures
from components.common_modules.constituent import Constituent
from utilities import logger


FORM = LIBRARY.timeml.FORM
STEM = LIBRARY.timeml.STEM
POS = LIBRARY.timeml.POS
POS_ADJ = LIBRARY.timeml.POS_ADJ
TENSE = LIBRARY.timeml.TENSE
ASPECT = LIBRARY.timeml.ASPECT
EPOS = LIBRARY.timeml.EPOS
POS_PREP = LIBRARY.timeml.POS_PREP
MOD = LIBRARY.timeml.MOD
POL = LIBRARY.timeml.POL
EVENTID = LIBRARY.timeml.EVENTID
EIID = LIBRARY.timeml.EIID
CLASS = LIBRARY.timeml.CLASS


def token_class(pos):
    """Returns the class that is appropriate for the part-of-speech."""
    return AdjectiveToken if pos.startswith(POS_ADJ) else Token


class Token(Constituent):

    """implements a single token.

    Instance variables:
        text        -  the text string of the token
        pos         -  the part-of-speech of the token
        event       -  set to True if the token is wrapped in an EventTag
        event_tag   -  contains the EventTag

    The event, eid and event are set at TarsqiTree creation for the daughters of
    event tags."""

    def __init__(self, word, pos):
        """Initialize with the word and a part-of-speech, use defaults for all
        the other variables."""
        Constituent.__init__(self)
        self.name = 'lex'
        self.text = word
        self.pos = pos
        self.event = None
        self.event_tag = None
        self.textIdx = None
        self.features = None
        self.checkedEvents = False

    def __str__(self):
        return "<Token %s:%s pos=%s %s>" % (self.begin, self.end, self.pos, self.text)

    def __getitem__(self, index):
        """The method with the same name on Constituent made sure that we can view the
        Token as something that has elements. But here we add that Token has
        itself as its one daughter. This is used by update_event_checked_marker
        in the chunks module."""
        if index == 0:
            return self
        else:
            raise IndexError("there is only one element in a Token")

    def feature_value(self, name):
        """Used by matchConstituent. Needs cases for all instance variables used in the
        pattern matching phase."""
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

    def getText(self):
        """Return the text of the token."""
        return self.text

    def isToken(self):
        """Returns True"""
        return True

    def isMainVerb(self):
        """Return True if self is a main verb and False if not."""
        return self.pos[0] == 'V' and self.getText() not in forms.auxVerbs

    def isPreposition(self):
        """Return True if self is a preposition and False if not. Note that this
        method returns False for the preposition in 'to the barn'."""
        return self.pos == POS_PREP

    def createEvent(self, imported_events=None):
        """Do nothing when an AdjectiveToken or Token is asked to create an
        event. Potential adjectival events are processed from the VerbChunk
        using the createAdjEvent() method. Do not log a warning since it is
        normal for a Token to be asked this, without this method a method with
        the same name on Consituent would log a warning."""
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
        print "%s<%s position=%d %d-%d pos=%s text=%s%s>" % \
            (indent * ' ', self.__class__.__name__, self.position,
             self.begin, self.end, self.pos, self.getText(), event_string)


class AdjectiveToken(Token):

    def feature_value(self, name):
        """Used by matchConstituent. Needs cases for all instance variables used in the
        pattern matching phase."""
        # TODO: this can probably be moved to Token and replace the method there
        if name == 'nodeType':
            return self.__class__.__name__
        elif name == 'text':
            return self.getText()
        elif name == 'pos':
            return self.pos
        elif name == 'nodeName':
            return self.pos
        # this is used by slinket/s2t in case the adjective is an event
        elif name in ['eventStatus', 'text', FORM, STEM, POS, TENSE, ASPECT,
                    EPOS, MOD, POL, EVENTID, EIID, CLASS]:
            if not self.event:
                return None
            if name == 'eventStatus':
                return '1'
            if name == 'text' or name == FORM:
                return self.tree.events[self.eid][FORM]
            if name == MOD:
                return self.tree.events[self.eid].get(MOD,'NONE')
            if name == POL:
                return self.tree.events[self.eid].get(POL,'POS')
            if name == POS:
                return self.tree.events[self.eid].get(POS,'NONE')
            return self.tree.events[self.eid][name]
        else:
            raise AttributeError, name

    def isAdjToken(self):
        return True
        
    def createAdjEvent(self, verbfeatures=None):
        """Processes the adjective after a copular verb and make it an event if the
        adjective has an event class."""
        logger.debug("AdjectiveToken.createAdjEvent(verbfeatures)")
        if not self.parent.__class__.__name__ == 'Sentence':
            logger.warn("Unexpected syntax tree")
            return
        self.features = AChunkFeatures(self, verbfeatures)
        logger.debug(self.features.as_verbose_string())
        self._conditionallyAddEvent()

    def _conditionallyAddEvent(self):
        """Check whether there is an event class and add the event to self.tree if
        there is one. There is a sister of this method on Chunk."""
        if self.features.evClass:
            self.tree.addEvent(Event(self.features))

"""tags.py

Contains classes for TimeML tags.

"""


from library.main import LIBRARY
from components.common_modules.constituent import Constituent
from utilities import logger
from utils import get_tokens


EVENT = LIBRARY.timeml.EVENT
TIMEX = LIBRARY.timeml.TIMEX
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK
TID = LIBRARY.timeml.TID
EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
EVENTID = LIBRARY.timeml.EVENTID
CLASS = LIBRARY.timeml.CLASS
TENSE = LIBRARY.timeml.TENSE
ASPECT = LIBRARY.timeml.ASPECT
EPOS = LIBRARY.timeml.EPOS
MOD = LIBRARY.timeml.MOD
POL = LIBRARY.timeml.POL
FORM = LIBRARY.timeml.FORM
STEM = LIBRARY.timeml.STEM
POS = LIBRARY.timeml.POS


class Tag(Constituent):

    """Abstract class for all TimeML non-link tags."""

    def createEvent(self, imported_events=None):
        """Do nothing when an EventTag or TimexTag is asked to create an
        event. Without this method the method with the same name on Constituent
        would log a warning."""
        pass


class EventTag(Tag):

    """Class for TimeML EVENT tags."""

    def __init__(self, attrs):
        Constituent.__init__(self)
        self.name = EVENT
        self.attrs = attrs
        self.eid = attrs[EID]
        self.eiid = attrs[EIID]
        self.eClass = attrs[CLASS]
        self.token = None

    def __str__(self):
        return "<EventTag %d:%d eid=%s>" % (self.begin, self.end, self.eid)

    def feature_value(self, name):
        # TODO: can probably use the local attrs dictionary for many of these
        if name == 'eventStatus':
            return '1'
        elif name == 'nodeType':
            return self.__class__.__name__
        elif name in (EVENTID, EIID, CLASS, TENSE, ASPECT, EPOS, STEM):
            return self.tree.events[self.eid][name]
        elif name == MOD:
            return self._get_attribute(name, 'NONE')
        elif name == POL:
            return self._get_attribute(name, 'POS')
        elif name in ('text', FORM):
            if self.tree.events.has_key(self.eid):
                return self.tree.events[self.eid][FORM]
            else:
                logger.warn("Event %s is not stored in the events on the TarsqiTree" % self)
                return ' '.join([t.text for t in get_tokens(self)])
        elif name == POS:
            try:
                return self.tree.events[self.eid][POS]
            except:
                # I don't remember whether POS has a particular use here
                # or is a left over from prior times
                logger.warn("Returning 'epos' instead of 'pos' value")
                return self.tree.events[self.eid][EPOS]
        else:
            raise AttributeError, name

    def _get_attribute(self, name, default):
        try:
            return self.tree.events[self.eid+'d'][name]
        except:
            return default

    def isEvent(self):
        return True

    def pretty_print(self, indent=0):
        (eid, eiid, cl) = (self.attrs.get('eid'), self.attrs.get('eiid'),
                           self.attrs.get('class'))
        print "%s<%s position=%s %d-%d eid=%s eiid=%s class=%s>" % \
            (indent * ' ', self.__class__.__name__, self.position,
             self.begin, self.end, eid, eiid, cl)
        for dtr in self.dtrs:
            dtr.pretty_print(indent+2)


class TimexTag(Tag):

    def __init__(self, attrs):
        Constituent.__init__(self)
        self.name = TIMEX
        self.attrs = attrs
        self.checkedEvents = False

    def __str__(self):
        return "<TimexTag %d:%d tid=%s>" % (self.begin, self.end, self.attrs[TID])

    def feature_value(self, name):
        if name == 'eventStatus':
            return '0'
        elif name == 'nodeType':
            return self.__class__.__name__
        elif name in ['text', FORM, STEM, POS, TENSE, ASPECT, EPOS, MOD, POL,
                      EVENTID, EIID, CLASS]:
            return None
        else:
            raise AttributeError, name

    def isTimex(self):
        return True

    def pretty_print(self, indent=0):
        print "%s<%s tid=%s type=%s value=%s>" % \
            (indent * ' ', self.__class__.__name__, self.attrs.get('tid'),
             self.attrs.get('type'), self.attrs.get('value'))
        for dtr in self.dtrs:
            dtr.pretty_print(indent+2)


class LinkTag():

    """Abstract class for all TimeML link tags. LinkTags are not constituents
    since they are never inserted in the hierarchical structure of a TarsqiTree,
    but they are added to lists of links in alink_list, slink_list and
    tlink_list.

    Instance variables
       name  - a string ('ALINK', 'SLINK' or 'TLINK')
       attrs - a dictionary of attributes"""

    def __init__(self, name, attrs):
        """Initialize name and attributes."""
        self.name = name
        self.attrs = attrs

    def __str__(self):
        return "<%s %s %s %s>" % (self.name, self.rel(),
                                  self.eiid1(), self.eiid2())

    def rel(self):
        return self.attrs.get('relType')

    def eiid1(self):
        """Return the eiid of the first event in the relation."""
        return self.attrs.get('eventInstanceID')

    def eiid2(self):
        """Return the eiid of the second event in the relation."""
        return self.attrs.get('relatedToEventInstance')


class AlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, ALINK, attrs)


class SlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, SLINK, attrs)

    def eiid2(self):
        """Return the eiid of the second event in the relation."""
        return self.attrs.get('subordinatedEventInstance')


class TlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, TLINK, attrs)

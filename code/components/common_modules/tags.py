"""tags.py

Contains classes for TimeML tags.

"""


from library.timeMLspec import EVENT, INSTANCE, TIMEX, ALINK, SLINK, TLINK
from library.timeMLspec import EID, EIID, EVENTID
from library.timeMLspec import CLASS, TENSE, ASPECT, EPOS, MOD, POL, FORM, STEM, POS
from components.common_modules.constituent import Constituent
from utilities import logger

# just here for now to track when __getattr__ is used (MV)
trackGetAttrUse = False
trackGetAttrUse = True


class Tag(Constituent):

    """Abstract class for all TimeML non-link tags."""

    def createEvent(self):
        """Do nothing when an EventTag or TimexTag is asked to create an event. Without
        this method the method with the same name on Constituent would log a warning."""
        pass



class EventTag(Tag):

    """Class for TimeML EVENT tags."""
    
    def __init__(self, attrs):
        """ The nodeType attribute is set to the same value as name because some methods
        ask for a nodeType attribute."""
        Constituent.__init__(self)
        self.name = EVENT
        self.nodeType = EVENT
        self.attrs = attrs
        self.eid = attrs[EID]
        self.eClass = attrs[CLASS]
        self.token = None

    def __str__(self):
        return "<EventTag name=%s eid=%s>" % (self.name, self.eid)


    def __getattr__(self, name):

        # TODO. This method is used occasionally so it cannot be removed. But
        # the way it is used does not make a lot of sense since it is not used
        # for attribute access but as a custom function for matching.

        # TODO: can probably use the local attrs dictionary for many of these,
        # but keep this till I figure out what the weird error is on wsj_0584 in
        # the slinket regression tests

        if trackGetAttrUse:
            print "*** EventTag.__getattr__('%s')" % name
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
            return self.tree.events[self.eid][FORM]
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
            return self.tree.events[self.eid][name]
        except:
            return 'NONE'

    def isEvent(self):
        return True

    def pretty_print(self, indent=0):
        (eid, eiid, cl) = (self.attrs.get('eid'), self.attrs.get('eiid'), self.attrs.get('class'))
        print "%s<%s position=%s %d-%d eid=%s eiid=%s class=%s>" % \
            (indent * ' ', self.name, self.position, self.begin, self.end, eid, eiid, cl)
        for dtr in self.dtrs:
            dtr.pretty_print(indent+2)


class TimexTag(Tag):

    """There is something fishy about this class because it all breaks when you try to
    print an instance. The problem probably stems from __getattr__."""
    
    def __init__(self, attrs):
        Constituent.__init__(self)
        # NOTE: need to standardize on using name or nodeType, but the latter is
        # there for matching puproses and may be removed when __getattr__ has
        # been revamped
        self.name = TIMEX
        self.nodeType = TIMEX
        self.attrs = attrs
        self.checkedEvents = False

    def XXX__getattr__(self, name):
        # TODO. This method caused weird problems. The code seems to run okay
        # without it, but it is used, typically for nodeType. Investigate what
        # it is used for and eliminate that use, which was already done for
        # nodeType. Need to test this more.
        if trackGetAttrUse:
            print "*** TimexTag.__getattr__", name
        if name == 'eventStatus':
            return '0'
        elif name in ['text', FORM, STEM, POS, TENSE, ASPECT, EPOS, MOD, POL,
                      EVENTID, EIID, CLASS]:
            return None
        else:
            raise AttributeError, name

    def isTimex(self):
        return True
        
    def pretty_print(self, indent=0):
        print "%s<%s tid=%s type=%s value=%s>" % \
            (indent * ' ', self.name, self.attrs.get('tid'),
             self.attrs.get('type'), self.attrs.get('value') )
        for dtr in self.dtrs:
            dtr.pretty_print(indent+2)


class LinkTag():

    """Abstract class for all TimeML link tags. LinkTags are not constituents since
    they are never inserted in the hierarchical structure of a TarsqiTree, but they
    are added to lists of links in alink_list, slink_list and tlink_list.

    Instance variables
       name  - a string ('ALINK', 'SLINK' or 'TLINK')
       attrs - a dictionary of attributes"""

    def __init__(self, name, attrs):
        """Initialize name and attributes."""
        self.name = name
        self.attrs = attrs

    def __str__(self):
        return "<%s %s %s %s>" % (self.name, self.rel(), self.eiid1(), self.eiid2())

    def rel(self):
        return self.attrs.get('relType')

    def eiid1(self):
        return self.attrs.get('eventInstanceID')

    def eiid2(self):
        return self.attrs.get('relatedToEventInstance')


class AlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, ALINK, attrs)


class SlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, SLINK, attrs)

    def eiid2(self):
        return self.attrs.get('subordinatedEventInstance')


class TlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, TLINK, attrs)

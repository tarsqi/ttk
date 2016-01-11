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
        this method a method with the same name on Consituent would log a warning."""
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

    def XXX__getattr__(self, name):
        # TODO: remove this once it is established that blinker and s2t work
        # without it, it does not appear to be used for Evita and for Slinket
        # the attributes that this is used for are just __nonzero__, __str__ and
        # __repr__ (and somehow the errors raised get trapped).
        if trackGetAttrUse:
            print "*** EventTag.__getattr__", name
        if name == 'eventStatus':
            return '1'
        elif name == TENSE:
            #print "TENSE:", tree.events[self.eid][TENSE]
            return tree.events[self.eid][TENSE]
        elif name == ASPECT:
            return tree.events[self.eid][ASPECT]
        elif name == EPOS: #NF_MORPH:
            return tree.events[self.eid][EPOS]#[NF_MORPH]
        elif name == MOD:
            try: mod = tree.events[self.eid][MOD]
            except: mod = 'NONE'
            return mod
        elif name == POL:
            try: pol = tree.events[self.eid][POL]
            except: pol = 'POS'
            return pol
        elif name == EVENTID:
            return tree.events[self.eid][EVENTID]
        elif name == EIID:
            return tree.events[self.eid][EIID]
        elif name == CLASS:
            return tree.events[self.eid][CLASS]
        elif name == 'text' or name == FORM:
            return tree.events[self.eid][FORM]
        elif name == STEM:
            return tree.events[self.eid][STEM]
        elif name == POS:
            try:
                return tree.events[self.eid][POS]
            except:
                # I don't remember whether POS has a particular use here
                # or is a left over from prior times
                logger.warn("Returning 'epos' instead of 'pos' value")  
                return tree.events[self.eid][EPOS]
        else:
            raise AttributeError, name

    def isEvent(self):
        return True

    def pretty_print(self, indent=0):
        (eid, eiid, cl) = (self.attrs.get('eid'), self.attrs.get('eiid'), self.attrs.get('class'))
        print "%s<%s position=%s eid=%s eiid=%s class=%s>" % \
              ( indent * ' ', self.name, self.position, str(eid), str(eiid), str(cl) )
        for dtr in self.dtrs:
            dtr.pretty_print(indent+2)


class TimexTag(Tag):

    """There is something fishy about this class because it all breaks when you try to
    print an instance. The problem probably stems from __getattr__."""
    
    def __init__(self, attrs):
        Constituent.__init__(self)
        # NOTE: need to standardize on using name or nodeType
        self.name = TIMEX
        self.nodeType = TIMEX
        self.attrs = attrs
        self.checkedEvents = False

    def XXX__getattr__(self, name):
        # TODO. This method caused weird problems. The code seems to run okay
        # without it, but it is used, typically for nodeType. Investigate what
        # it is used for and eliminate that use, which was already done for
        # nodeType.
        if trackGetAttrUse:
            print "*** TimexTag.__getattr__", name
        if name == 'eventStatus':
            return '0'
        elif name in ['text', FORM, STEM, POS, TENSE, ASPECT, EPOS, MOD, POL,
                      EVENTID, EIID, CLASS]: #NF_MORPH, 
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


class AlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, ALINK, attrs)


class SlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, SLINK, attrs)


class TlinkTag(LinkTag):

    def __init__(self, attrs):
        LinkTag.__init__(self, TLINK, attrs)

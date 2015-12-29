#from string import lower

from library.timeMLspec import EIID, TENSE, ASPECT, EPOS, POL, MOD, CLASS, POS, FORM, STEM
from library.timeMLspec import VERB, NOUN, ADJECTIVE
from library.slinket.main import SLINKET_DICTS
from utilities import logger


class EventExpression:

    """Class that wraps an event in a way that's convenient for Slinket.

    Instance variables:

       dict
       eid
       eiid
       tense
       aspect
       nf_morph
       polarity
       modality
       evClass
       pos
       form

       locInSent - idx of node bearing event tag in the document, wrt to its
                   sentence parent node.
       eventNum - position of event in sentence.eventList (needed for
                  potential slinking w/ previous or next events in list)
       isSlinking - an integer, set to 0 at initialization, does not seem to
                    be used
       
    """

    # TODO: move this class to main.py, it is not worthy of having its own
    # module and many if not all of the needed imports are done there as well.


    def __init__(self, eid, locInSent, eventNum, event_attributes):
        """Set all attributes, using default values if appropriate.
        Arguments:
           eid - a string
           locInSent - an integer
           eventNum - an integer
           dict - a dictionary with event attributes"""
        self.locInSent = locInSent
        self.eventNum = eventNum
        self.dict = event_attributes
        self.eid = eid
        self.eiid = self.get_event_attribute(EIID)
        self.tense = self.get_event_attribute(TENSE)
        self.aspect = self.get_event_attribute(ASPECT)
        self.nf_morph = self.get_event_attribute(EPOS)
        self.polarity = self.get_event_attribute(POL, optional=True)
        self.modality = self.get_event_attribute(MOD, optional=True)
        self.evClass = self.get_event_attribute(CLASS)
        self.pos = self.get_event_attribute(POS)
        self.form = self.get_event_attribute(FORM)
        #self.isSlinking = 0

    def as_verbose_string(self):
        return \
            "%s: %s\n" % (self.__class__.__name__, self.form) + \
            "\tpos=%s TENSE=%s ASPECT=%s CLASS=%s\n" \
            % (self.pos, self.tense, self.aspect, self.evClass) + \
            "\tNF_MORPH=%s MODALITY=%s POLARITY=%s\n" \
            % (self.nf_morph, self.modality, self.polarity) + \
            "\tCLASS=%s locInSent=%s eventNum=%s\n" \
            % (self.evClass, self.locInSent, self.eventNum)

    def get_event_attribute(self, attr, optional=False):
        """Return the value of an attribute 'attr' from self.dict. If the attribute is
        not in the dictionary, then (i) return a default value if there is one,
        and (ii) write an error if the attribute is not optional."""
        val = self.dict.get(attr)
        if val is None and not optional:
            logger.error("No %s attribute for current event" % attr)
        if val is None and attr == POL:
            val = 'POS'
        return val

    def pp(self):
        self.pretty_print()
        
    def pretty_print(self):
        print self.as_verbose_string()

    def can_introduce_alink(self):
        """Returns True if the EventExpression instance can introduce an Alink, False
        otherwise. This ability is determined by dictionary lookup."""
        form = self.form.lower()
        if self.nf_morph == VERB:
            return SLINKET_DICTS.alinkVerbsDict.has_key(form)
        if self.nf_morph == NOUN:
            return SLINKET_DICTS.alinkNounsDict.has_key(form)
        return False

    def can_introduce_slink(self):
        """Returns True if the EventExpression instance can introduce an Slink, False
        otherwise. This ability is determined by dictionary lookup."""
        form = self.form.lower()
        if self.nf_morph == VERB:
            return SLINKET_DICTS.slinkVerbsDict.has_key(form)
        if self.nf_morph == NOUN:
            return SLINKET_DICTS.slinkNounsDict.has_key(form)
        if self.nf_morph == ADJECTIVE:
            return SLINKET_DICTS.slinkAdjsDict.has_key(form)
        return False

    def alinkingContexts(self, key):
        """Returns the list of alink patterns from the dictionary."""
        form = self.form.lower()
        if self.nf_morph == VERB:
            pattern_dictionary = SLINKET_DICTS.alinkVerbsDict
        elif self.nf_morph == NOUN:
            pattern_dictionary = SLINKET_DICTS.alinkNounsDict
        else:
            logger.warn("SLINKS of type "+str(key)+" for EVENT form "+str(form)+" should be in the dict")
            return []
        return pattern_dictionary.get(form,{}).get(key,[])
        
    def slinkingContexts(self, key):
        """Returns the list of slink patterns from the dictionary."""
        form = self.form.lower()
        if self.nf_morph == VERB:
            pattern_dictionary = SLINKET_DICTS.slinkVerbsDict
        elif self.nf_morph == NOUN:
            pattern_dictionary = SLINKET_DICTS.slinkNounsDict
        elif self.nf_morph == ADJECTIVE:
            pattern_dictionary = SLINKET_DICTS.slinkAdjsDict
        else:
            logger.warn("SLINKS of type "+str(key)+" for EVENT form "+str(form)+" should be in the dict")
            return []
        return pattern_dictionary.get(form,{}).get(key,[])

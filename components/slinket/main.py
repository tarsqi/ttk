"""Main module for the Slinket component.

Responsible for the top-level processing of Slinket. Most functionality is in
the Chunk class.

"""


from components.common_modules.component import TarsqiComponent
from components.common_modules.utils import get_events, get_words_as_string
from library.slinket.main import SLINKET_DICTS
from library.tarsqi_constants import SLINKET
from library.main import LIBRARY
from utilities import logger

DEBUG = False


class Slinket (TarsqiComponent):

    """Class that implements the Slinket SLINK and ALINK parser. Only lexical alinks
    and slinks are found.

    Purpose clause are not yet implemented. But note that some purpose clause
    SLINKS are already introduced in the lexically-triggered process. This is so
    for those events that discoursively tend to appear modified by a Purpose
    Clause (e.g., 'address'). The data are based on TimeBank. Conditionals are
    not implemented either.

    Instance variables:
       NAME - a string
       doctree - a TarsqiTree
       docelement - a docelement Tag

    """

    def __init__(self):
        """Initialize Slinket. Sets doctree and docelement to None, these are added by
        process_doctree()."""
        self.NAME = SLINKET
        self.doctree = None
        self.docelement = None
        # Load the Slinket dictionaries if they have not been loaded yet
        SLINKET_DICTS.load()

    def process_doctree(self, doctree):
        """Find alinks and slinks in doctree and export them to self.docelement."""
        self.doctree = doctree
        if DEBUG:
            for s in doctree:
                for e in s:
                    print e
                    e.print_vars()
            doctree.pp()
        self.docelement = self.doctree.docelement
        self._build_event_dictionary()
        for sentence in self.doctree:
            # print get_words_as_string(sentence)
            self._find_links(self.doctree, sentence)
        self._add_links_to_document()

    def _build_event_dictionary(self):
        """Creates a dictionary with events on the self.doctree variable and adds
        event lists (which consist of pairs of event location and event id) to
        all sentences in self.doctree."""
        self.doctree.events = {}
        for event in get_events(self.doctree):
            eid = event.attrs[LIBRARY.timeml.EID]
            self.doctree.events[eid] = event.attrs
            pos = event.dtrs[0].pos
            epos = self.doctree.events[eid][LIBRARY.timeml.POS]
            form = event.dtrs[0].getText()
            self.doctree.events[eid][LIBRARY.timeml.FORM] = form
            self.doctree.events[eid][LIBRARY.timeml.EPOS] = epos
            self.doctree.events[eid][LIBRARY.timeml.POS] = pos
        for sentence in self.doctree:
            sentence.set_event_list()

    def _find_links(self, doc, sentence):
        """For each event in the sentence, check whether an Alink or Slink can be
        created for it."""
        eventNum = -1
        for (eLocation, eid) in sentence.eventList:
            eventNum += 1
            event_expr = EventExpression(eid, eLocation, eventNum, doc.events[eid])
            logger.debug(event_expr.as_verbose_string())
            if event_expr.can_introduce_alink():
                logger.debug("Alink candidate: " + event_expr.form)
                self._find_alink(sentence, event_expr)
            if event_expr.can_introduce_slink():
                logger.debug("Slink candidate: " + event_expr.form)
                self._find_lexically_based_slink(sentence, event_expr)

    def _find_alink(self, sentence, event_expr):
        """Try to find an alink with event_expr as the trigger, alinks are created as a side
        effect."""
        evNode = sentence[event_expr.locInSent]
        if evNode is None:
            logger.error("No node found at locInSent=%s" % event_expr.locInSent)
            return
        forwardFSAs = event_expr.alinkingContexts('forward')
        if forwardFSAs:
            alink_created = evNode.find_forward_alink(forwardFSAs)
        if not alink_created:
            backwardFSAs = event_expr.alinkingContexts('backwards')
            if backwardFSAs:
                evNode.find_backward_alink(backwardFSAs)

    def _find_lexically_based_slink(self, sentence, event_expr):
        """Try to find lexically based Slinks for an instance of EventExpression using
        forward, backward and reporting FSA paterns. No return value, if an
        Slink is found, it will be created by the chunk that embeds the Slink
        triggering event."""
        evNode = sentence[event_expr.locInSent]
        if evNode is None:
            logger.error("No node found at locInSent=%s" % event_expr.locInSent)
            return
        slink_created = False
        logger.debug("Sentence element class: %s" % evNode.__class__.__name__)
        forwardFSAs = event_expr.slinkingContexts('forward')
        if forwardFSAs:
            logger.debug("Applying FORWARD slink FSAs")
            slink_created = evNode.find_forward_slink(forwardFSAs)
            logger.debug("forward slink created = %s" % slink_created)
        if not slink_created:
            backwardFSAs = event_expr.slinkingContexts('backwards')
            if backwardFSAs:
                logger.debug("Applying BACKWARD slink FSAs")
                slink_created = evNode.find_backward_slink(backwardFSAs)
                logger.debug("backward slink created = %s" % slink_created)
        if not slink_created:
            reportingFSAs = event_expr.slinkingContexts('reporting')
            if reportingFSAs:
                logger.debug("Applying REPORTING slink FSAs")
                slink_created = evNode.find_reporting_slink(reportingFSAs)
            logger.debug("reporting slink created = %s" % slink_created)

    def _add_links_to_document(self):
        for alink in self.doctree.alinks:
            self._add_link(LIBRARY.timeml.ALINK, alink.attrs)
        for slink in self.doctree.slinks:
            self._add_link(LIBRARY.timeml.SLINK, slink.attrs)

    def _add_link(self, tagname, attrs):
        """Add the link to the TagRepository instance on the TarsqiDocument."""
        attrs[LIBRARY.timeml.ORIGIN] = SLINKET
        logger.debug("Adding %s: %s" % (tagname, attrs))
        self.doctree.tarsqidoc.tags.add_tag(tagname, -1, -1, attrs)


class EventExpression:

    """Class that wraps an event in a way that's convenient for Slinket.

    Instance variables:
       dict        -  dictionary of event attributes
       eid
       eiid
       tense
       aspect
       nf_morph    -  VERB, NOUN or ADJECTIVE, sometimes called epos
       polarity    -  optional attribute (that is, it can be None)
       modality    -  optional attribute (that is, it can be None)
       evClass     -  the event class
       pos         -  the part-of-speech of the event token
       form        -  the actual string
       locInSent   -  idx of node bearing event tag in the document, wrt to its
                      sentence parent node.
       eventNum    -  position of event in sentence.eventList (needed for
                      potential slinking with previous or next events in list)
    """

    def __init__(self, eid, locInSent, eventNum, event_attributes):
        """Set all attributes, using default values if appropriate. The arguments are:
        an identifier string, an integer reflecting the location of the event in
        the sentence, an integer reflecting the position of the event on the
        eventList on the sentence and a dictionary with event attributes."""
        self.locInSent = locInSent
        self.eventNum = eventNum
        self.dict = event_attributes
        self.eid = eid
        self.eiid = self.get_event_attribute(LIBRARY.timeml.EIID)
        self.tense = self.get_event_attribute(LIBRARY.timeml.TENSE)
        self.aspect = self.get_event_attribute(LIBRARY.timeml.ASPECT)
        self.nf_morph = self.get_event_attribute(LIBRARY.timeml.EPOS)
        self.polarity = self.get_event_attribute(LIBRARY.timeml.POL, optional=True)
        self.modality = self.get_event_attribute(LIBRARY.timeml.MOD, optional=True)
        self.evClass = self.get_event_attribute(LIBRARY.timeml.CLASS)
        self.pos = self.get_event_attribute(LIBRARY.timeml.POS)
        self.form = self.get_event_attribute(LIBRARY.timeml.FORM)

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
        if val is None and attr == LIBRARY.timeml.POL:
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
        if self.nf_morph == LIBRARY.timeml.VERB:
            return form in SLINKET_DICTS.alinkVerbsDict
        if self.nf_morph == LIBRARY.timeml.NOUN:
            return form in SLINKET_DICTS.alinkNounsDict
        return False

    def can_introduce_slink(self):
        """Returns True if the EventExpression instance can introduce an Slink, False
        otherwise. This ability is determined by dictionary lookup."""
        form = self.form.lower()
        if self.nf_morph == LIBRARY.timeml.VERB:
            return form in SLINKET_DICTS.slinkVerbsDict
        if self.nf_morph == LIBRARY.timeml.NOUN:
            return form in SLINKET_DICTS.slinkNounsDict
        if self.nf_morph == LIBRARY.timeml.ADJECTIVE:
            return form in SLINKET_DICTS.slinkAdjsDict
        return False

    def alinkingContexts(self, key):
        """Returns the list of alink patterns from the dictionary."""
        form = self.form.lower()
        if self.nf_morph == LIBRARY.timeml.VERB:
            pattern_dictionary = SLINKET_DICTS.alinkVerbsDict
        elif self.nf_morph == LIBRARY.timeml.NOUN:
            pattern_dictionary = SLINKET_DICTS.alinkNounsDict
        else:
            logger.warn("SLINKS of type " + str(key) + " for EVENT form " +
                        str(form) + " should be in the dict")
            return []
        return pattern_dictionary.get(form, {}).get(key, [])

    def slinkingContexts(self, key):
        """Returns the list of slink patterns from the dictionary."""
        form = self.form.lower()
        if self.nf_morph == LIBRARY.timeml.VERB:
            pattern_dictionary = SLINKET_DICTS.slinkVerbsDict
        elif self.nf_morph == LIBRARY.timeml.NOUN:
            pattern_dictionary = SLINKET_DICTS.slinkNounsDict
        elif self.nf_morph == LIBRARY.timeml.ADJECTIVE:
            pattern_dictionary = SLINKET_DICTS.slinkAdjsDict
        else:
            logger.warn("SLINKS of type " + str(key) + " for EVENT form " +
                        str(form) + " should be in the dict")
            return []
        return pattern_dictionary.get(form, {}).get(key, [])

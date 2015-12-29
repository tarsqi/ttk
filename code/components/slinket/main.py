"""

Main module for the Slinket component.

Responsible for the top-level processing of Slinket.

"""

from EventExpression import EventExpression

from components.common_modules.component import TarsqiComponent
from library.slinket.main import SLINKET_DICTS
from library.tarsqi_constants import SLINKET
from library.timeMLspec import ALINK, SLINK, EVENT, INSTANCE
from library.timeMLspec import EID, EIID, EVENTID, POS, EPOS, FORM
from utilities import logger
from utilities.converter import FragmentConverter
from docmodel.xml_parser import Parser, XmlDocElement
from docmodel.xml_parser import create_content_string



class Slinket (TarsqiComponent):

    """Class that implements the Slinket SLINK and ALINK parser. Only lexical alinks
    and slinks are found.

    Purpose clause are not yet implemented. But note that some purpose clause SLINKS are
    already introduced in the lexically-triggered process. This is so for those events
    that discoursively tend to appear modified by a Purpose Clause (e.g., 'address'). The
    data are based on TimeBank. Conditionals are not implemented either.

    Instance variables:
       NAME - a string
       doctree - a Document

    """

    
    def __init__(self):
        """Load the Slinket dictionaries if they have not been loaded yet."""
        self.NAME = SLINKET
        self.doctree = None
        SLINKET_DICTS.load()
        
    def process_file(self, infile, outfile):
        """Run Slinket on the input file and write the results to the output file."""
        pass

    def process_doctree(self, doctree, tarsqidocelement):
        """Find alinks and slinks in dcotree and export them to tarsqidocelement."""
        self.doctree = doctree
        self.docelement = tarsqidocelement
        self._build_event_dictionary()
        #doctree.pp()
        for sentence in self.doctree:
            self._find_links(self.doctree, sentence)
        for alink in self.doctree.alink_list:
            self.add_link(ALINK, alink.attrs)
        for slink in self.doctree.slink_list:
            self.add_link(SLINK, slink.attrs)

    def add_link(self, tagname, attrs):
        """Add the link to the TagRepository instance on the TarsqiDocElement."""
        logger.debug("Adding %s: %s" % (tagname, attrs))
        self.docelement.tarsqi_tags.add_tag(tagname, -1, -1, attrs)

    def _build_event_dictionary(self):
        """Creates a dictionary with events on the self.doctree variable and
        adds event lists to all sentences in self.doctree."""
        events = self.doctree.get_events()
        self.doctree.taggedEventsDict = {}
        for event in events:
            eid = event.attrs[EID]
            self.doctree.taggedEventsDict[eid] = event.attrs
            pos = event.dtrs[0].pos
            epos = self.doctree.taggedEventsDict[eid][POS]
            form = event.dtrs[0].getText()
            self.doctree.taggedEventsDict[eid][FORM] = form
            self.doctree.taggedEventsDict[eid][EPOS] = epos
            self.doctree.taggedEventsDict[eid][POS] = pos
        for sentence in self.doctree:
            sentence.set_event_list()

    def _find_links(self, doc, sentence):
        """For each event in the sentence, check whether an Alink or Slink can be
        created for it."""
        self.currSent = sentence
        eventNum = -1
        for (eLocation, eid) in self.currSent.eventList:
            eventNum += 1
            event_expr = EventExpression(eid, eLocation, eventNum, doc.taggedEventsDict[eid])
            logger.debug(event_expr.as_verbose_string())
            if event_expr.can_introduce_alink():
                logger.debug("Alink candidate: " + event_expr.form)
                self._find_alink(event_expr)
            if event_expr.can_introduce_slink():
                logger.debug("Slink candidate: " + event_expr.form)
                self._find_lexically_based_slink(event_expr)

    def _find_alink(self, event_expr):
        """Try to find an alink with event_expr as the trigger, alinks are created as a side
        effect."""
        evNode = self.currSent[event_expr.locInSent]
        if evNode is None:
            logger.warning("No event node found at locInSent")
            return
        forwardFSAs = event_expr.alinkingContexts('forward')
        if forwardFSAs:
            alink_created = evNode.find_forward_alink(forwardFSAs)
        if not alink_created:
            backwardFSAs = event_expr.alinkingContexts('backwards')
            if backwardFSAs:
                evNode.find_backward_alink(backwardFSAs)

    def _find_lexically_based_slink(self, event_expr):
        """Try to find lexically based Slinks for an instance of EventExpression using
        forward, backward and reporting FSA paterns. No return value, if an
        Slink is found, it will be created by the chunk that embeds the Slink
        triggering event."""
        evNode = self.currSent[event_expr.locInSent]
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

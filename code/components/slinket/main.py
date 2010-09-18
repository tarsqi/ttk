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

    """Class that implements the Slinket SLINK and ALINK parser. 

    Only lexical alinks and slinks are found.

    Purpose clause are not yet implemented. But note that some purpose clause SLINKS are
    already introduced in the lexically-triggered process. This is so for those events
    that discoursively tend to appear modified by a Purpose Clause (e.g., 'address'). The
    data are based on TimeBank.

    Conditionals are not implemented either.

    Instance variables:
       NAME - a string
       doctree - a Document"""

    
    def __init__(self):

        """Load the Slinket dictionaries if they have not been loaded yet."""

        self.NAME = SLINKET
        self.doctree = None
        SLINKET_DICTS.load()

        
    def process_file(self, infile, outfile):

        """Run Slinket on the input file and write the results to the output file. Both input an
        doutput file are fragments. Uses the xml parser as well as the fragment converter
        to prepare the input and create the shallow tree that Slinket requires.

        Arguments:
           infile - an absolute path
           outfile - an absolute path"""

        xmldoc = Parser().parse_file(open(infile,'r'))
        self.process_xml_doc(xmldoc)
        self.doctree.printOut(outfile)

        
    def process_xmldoc(self, xmldoc):

        """Process an XmlDocument fragment and add alinks and slinks to it.

        Arguments:
            xmldoc - an XmlDocument """

        def add_link(tagname, attrs, position):
            """Add opening and closing link at position in an XmlDocument."""
            links_str = create_content_string(tagname, attrs)
            open_link = XmlDocElement(links_str, tagname, attrs)
            close_link = XmlDocElement('</'+tagname+'>', tagname)
            position.insert_element_before(open_link)
            position.insert_element_before(close_link)

        self.xmldoc = xmldoc
        self.xmldoc_closingtag = self.xmldoc.get_closing_tag()

        # find alinks and slinks
        self.doctree = FragmentConverter(xmldoc).convert()
        self._build_event_dictionary()
        for sentence in self.doctree:
            self._find_links(self.doctree, sentence)

        # export links from the document tree into the xml document
        for alink in self.doctree.alink_list:
            add_link(ALINK, alink.attrs, self.xmldoc_closingtag)
        for slink in self.doctree.slink_list:
            add_link(SLINK, slink.attrs, self.xmldoc_closingtag)

        
    def _build_event_dictionary(self):

        """Creates a dictionary with events on the self.doctree variable and adds event lists to
        all sentences in self.doctree."""

        instances = {}
        for instance in self.xmldoc.get_tags(INSTANCE):
            instances[instance.attrs[EVENTID]] = instance.attrs
        self.doctree.taggedEventsDict = {}
        for event in self.xmldoc.get_tags(EVENT):
            eid = event.attrs[EID]
            self.doctree.taggedEventsDict[eid] = event.attrs
            self.doctree.taggedEventsDict[eid].update(instances[eid])
            # Now get the form and the part of speech. This is a bit tricky since it
            # relies on the fact that an opening event tag is is always followed by an
            # opening lex tag, which is then followed by plain text.
            pos = event.next.attrs[POS]
            #perhaps lex tag should know its form?
            form = event.next.next.content
            self.doctree.taggedEventsDict[eid][FORM] = form
            self.doctree.taggedEventsDict[eid][EPOS] = self.doctree.taggedEventsDict[eid][POS]
            self.doctree.taggedEventsDict[eid][POS] = pos

        for sentence in self.doctree:
            sentence.set_event_list()

        
    def _find_links(self, doc, sentence):

        """For each event in the sentence, check whether an Alink or Slink can be created for
        it."""

        self.currSent = sentence
        eventNum = -1
        for (eLocation, eId) in self.currSent.eventList:
            eventNum += 1
            event_expr = EventExpression(eId, eLocation, eventNum,
                                         doc.taggedEventsDict[eId])
            if event_expr.can_introduce_alink():
                logger.debug("EVENT: '"+event_expr.form+"' is candidate to Alinking")
                self._find_alink(event_expr)
            if event_expr.can_introduce_slink() :
                logger.debug("EVENT: '"+event_expr.form+"' is candidate to Slinking")
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

        """Try to find lexically based Slinks using forward, backward and reporting FSA
        paterns. No return value, if an Slink is found, it will be created by the chunk
        that embeds the Slink triggering event.

        Arguments:
           event_expr - an EventExpression"""

        evNode = self.currSent[event_expr.locInSent]
        if evNode is None:
            logger.error("No event node found at locInSent")
            return

        slink_created = False
        
        forwardFSAs = event_expr.slinkingContexts('forward')
        if forwardFSAs:
            slink_created = evNode.find_forward_slink(forwardFSAs)

        if not slink_created:
            backwardFSAs = event_expr.slinkingContexts('backwards')
            if backwardFSAs:
                logger.debug("PROCESS for BACKWARD slinks")
                slink_created = evNode.find_backward_slink(backwardFSAs)
            
        if not slink_created:
            reportingFSAs = event_expr.slinkingContexts('reporting')
            if reportingFSAs:
                logger.debug("PROCESS for REPORTING slinks")
                evNode.find_reporting_slink(reportingFSAs)


            

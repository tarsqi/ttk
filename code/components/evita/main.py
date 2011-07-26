"""Main module for Evita, the event recognition component.

Responsible for the top-level processing of Evita.

"""

from components.evita.gramChunk import getWordList, getPOSList
from components.common_modules.component import TarsqiComponent
from docmodel.xml_parser import Parser
from library.tarsqi_constants import EVITA
from utilities import logger
from utilities.converter import FragmentConverter



class Evita (TarsqiComponent):

    """Class that implements Evita's event recognizer.

    Instance variables:
       NAME - a string
       doctree - a Document instance """
    

    def __init__(self):

        """Set the NAME instance variable."""

        self.NAME = EVITA

        
    def process_file(self, infile, outfile):

        """Process a fragment file and write a file with EVENT tags.

        Arguments:
           infile - an absolute path
           outfile - an absolute path"""

        self.xmldoc = Parser().parse_file(open(infile,'r'))
        self.doctree = FragmentConverter(xmldoc, infile).convert()
        #self.pp_doctree(EVITA)
        self.extractEvents()
        xmldoc.save_to_file(outfile)

        
    def process_xmldoc(self, xmldoc):

        """Process an XmlDocument fragment and return one with EVENT tags

        Arguments:
            xmldoc - an instance of an XmlDocument object"""

        self.xmldoc = xmldoc
        self.doctree = FragmentConverter(xmldoc).convert()
        #self.pp_xmldoc(EVITA)
        #self.pp_doctree(EVITA)
        self.extractEvents()

        
    def process_string(self, instring):

        """Process a fragment string and return a string with EVENT tags.

        Arguments:
           instring - an XML string"""

        self.xmldoc = Parser().parse_string(instring)
        self.doctree = FragmentConverter(xmldoc).convert()
        self.extractEvents()
        return xmldoc.toString()

    
    def extractEvents(self):

        """Loop through all sentences in self.doctree and through all nodes in each
        sentence and determine if the node contains an event."""

        for sentence in self.doctree:
            #print "<sentence>\n"
            logger.debug("> SENTENCE:" + str(getWordList(sentence)))
            for node in sentence:
                #print node
                #node.pretty_print()
                #print "  checked=" + str(node.flagCheckedForEvents)
                #print
                if not node.flagCheckedForEvents:
                    node.createEvent()

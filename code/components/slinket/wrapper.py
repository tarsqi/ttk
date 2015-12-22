"""

Contains the Slinket wrapper.

"""

from library.tarsqi_constants import SLINKET
from components.slinket.main import Slinket
from components.common_modules import document
from utilities import logger


class SlinketWrapper:

    """Wrapper for Slinket. """


    def __init__(self, document):

        self.component_name = SLINKET
        self.document = document
        
        
    def process(self):

        """Retrieve the XmlDocument and hand it to Slinket for processing. Slinket
        processing will update this slice when events are added."""

        for element in self.document.elements:
            #element.tarsqi_tags.pp()
            doc = document.create_document_from_tarsqi_doc_element(element)
            Slinket().process_doctree(doc)

        #xmldocs = [self.document.xmldoc]
        #for xmldoc in xmldocs:
        #    xmldoc.reset()
        #    Slinket().process_xmldoc(xmldoc)

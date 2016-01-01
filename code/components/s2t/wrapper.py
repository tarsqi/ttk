"""

Contains the S2tWrapper.

"""

from library.tarsqi_constants import S2T
from components.s2t.main import Slink2Tlink


class S2tWrapper:

    """Wraps the S2T components. See ComponentWrapper for the instance variables."""

    
    def __init__(self, document):

        self.component_name = S2T
        self.document = document
        
        
    def process(self):

        """Retrieve the XmlDocument and hand it to S2T for processing. Processing will
        update this slice."""

        xmldocs = [self.document.xmldoc]
        for xmldoc in xmldocs:
            xmldoc.reset()
            Slink2Tlink().process_xmldoc(xmldoc)

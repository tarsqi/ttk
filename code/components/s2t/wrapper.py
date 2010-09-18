"""

Contains the S2tWrapper.

"""

from time import time
from ttk_path import TTK_ROOT
from library.tarsqi_constants import S2T
from components.s2t.main import Slink2Tlink
from utilities import logger


class S2tWrapper:

    """Wraps the S2T components. See ComponentWrapper for the instance variables."""

    
    def __init__(self, document, tarsqi_instance):

        self.component_name = S2T
        self.document = document
        
        
    def process(self):

        """Retrieve the XmlDocument and hand it to S2T for processing. Processing will update this
        slice."""

        begin_time = time()
        xmldocs = [self.document.xmldoc]
        for xmldoc in xmldocs:
            xmldoc.reset()
            Slink2Tlink().process_xmldoc(xmldoc)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

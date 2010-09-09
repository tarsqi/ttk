"""

Contains the Slinket wrapper.

"""

from time import time
from library.tarsqi_constants import SLINKET
from components.common_modules.component import ComponentWrapper
from components.slinket.main import Slinket
from utilities import logger


class SlinketWrapper(ComponentWrapper):

    """Wrapper for Slinket. See ComponentWrapper for more details on how
    component wrappers work. """


    def __init__(self, tag, xmldoc, tarsqi_instance):

        """Calls __init__ of the base class and sets component_name,
        parser, CREATION_EXTENSION and RETRIEVAL_EXTENSION."""

        ComponentWrapper.__init__(self, tag, xmldoc, tarsqi_instance)
        self.component_name = SLINKET

        
    def process(self):

        """Retrieve the slice from the XmlDocument and hand this slice to
        Evita for processing. Evita processing will update this slice
        when events are added. No arguments and no return value."""

        begin_time = time()
        xmldocs = self.document.get_tag_contents_as_xmldocs(self.tag)
        for xmldoc in xmldocs:
            Slinket().process_xmldoc(xmldoc)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

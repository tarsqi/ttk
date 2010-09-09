"""

Contains the Blinker wrapper.

"""

from time import time
from library.tarsqi_constants import BLINKER
from components.common_modules.component import ComponentWrapper
from components.blinker.main import Blinker
from utilities import logger


class BlinkerWrapper(ComponentWrapper):

    """Wrapper for Blinker. See ComponentWrapper for more details on how
    component wrappers work and on the instance variables."""

    
    def __init__(self, tag, xmldoc, tarsqi_instance):

        """Calls __init__ of the base class and sets component_name and dct
        values."""
        
        ComponentWrapper.__init__(self, tag, xmldoc, tarsqi_instance)
        self.dct = self.tarsqi_instance.metadata['dct']
        self.component_name = BLINKER

        
    def process(self):

        """Retrieve the slice from the XmlDocument and hand this slice to
        Evita for processing. Evita processing will update this slice
        when events are added. No arguments and no return value."""

        begin_time = time()
        xmldocs = self.document.get_tag_contents_as_xmldocs(self.tag)
        for xmldoc in xmldocs:
            Blinker().process_xmldoc(xmldoc, self.dct)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

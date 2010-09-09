"""

Contains the S2tWrapper.

"""

from time import time
from ttk_path import TTK_ROOT
from library.tarsqi_constants import S2T
from components.common_modules.component import ComponentWrapper
from components.s2t.main import Slink2Tlink
from utilities import logger


class S2tWrapper(ComponentWrapper):

    """Wraps the S2T components. See ComponentWrapper for the instance variables."""

    
    def __init__(self, tag, xmldoc, tarsqi_instance):

        """Calls __init__ of the base class and sets component_name."""

        ComponentWrapper.__init__(self, tag, xmldoc, tarsqi_instance)
        self.component_name = S2T

        
    def process(self):

        """Retrieve the slice from the XmlDocument and hand this slice to
        Evita for processing. Evita processing will update this slice
        when events are added. No arguments and no return value."""

        begin_time = time()
        xmldocs = self.document.get_tag_contents_as_xmldocs(self.tag)
        for xmldoc in xmldocs:
            Slink2Tlink().process_xmldoc(xmldoc)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

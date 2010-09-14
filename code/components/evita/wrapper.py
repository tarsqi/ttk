"""

Contains the Evita wrapper.

"""

from time import time
from library.tarsqi_constants import EVITA
from components.common_modules.component import ComponentWrapper
from components.evita.main import Evita
from utilities import logger


class EvitaWrapper(ComponentWrapper):

    """Wrapper for Evita. See ComponentWrapper for more details on how component wrappers
    work."""


    def __init__(self, tag, xmldoc, tarsqi_instance):

        """Sets instance variables."""

        ComponentWrapper.__init__(self, tag, xmldoc, tarsqi_instance)
        self.component_name = EVITA

        
    def process(self):

        """Retrieve the slices from the XmlDocument and hand these slice to Evita for
        processing. Evita processing will update the slices when events are added. No
        arguments and no return value."""

        begin_time = time()
        xmldocs = self.document.get_tag_contents_as_xmldocs(self.tag)
        for xmldoc in xmldocs:
            Evita().process_xmldoc(xmldoc)
        logger.info("%s DONE, processing time was %.3f seconds" %
                    (self.component_name, time() - begin_time))

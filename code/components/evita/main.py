"""Main module for Evita, the event recognition component.

Responsible for the top-level processing of Evita.

"""

import StringIO
from xml.sax.saxutils import escape, quoteattr

from components.evita.gramChunk import getWordList, getPOSList
from components.common_modules.component import TarsqiComponent
from components.common_modules.document import create_document_from_tarsqi_doc_element
from library.tarsqi_constants import EVITA
from utilities import logger


class Evita (TarsqiComponent):

    """Class that implements Evita's event recognizer. Instance variables: NAME: a string,
    doctree: a Document instance."""

    def __init__(self, tarsqidoc=None):
        """Set the NAME instance variable. The doctree variables is filled in during
        processing."""
        self.NAME = EVITA
        self.doctree = None         # instance of Document
        self.tarsqidoc = tarsqidoc  # instance of TarsqiDocument

    def process_element(self, element):
        """Process an instance of docmodel.document.TarsqiDocParagraph. Note that
        contrary to the other processing methods (preprocessor and gutime), in
        this case the doctree variable on the Evita instance is for just one
        element and not for the whole document or string. Events are added to
        the tag repository on the element."""
        self.tarsqidoc = element.doc
        self.doctree = create_document_from_tarsqi_doc_element(element)
        self.doctree.tarsqidoc = self.tarsqidoc
        self.extractEvents()

    def extractEvents(self):
        """Loop through all sentences in self.doctree and through all nodes in each
        sentence and determine if the node contains an event."""
        for sentence in self.doctree:
            logger.debug("SENTENCE: %s" % ' '.join(getWordList(sentence)))
            for node in sentence:
                if not node.checkedEvents:
                    node.createEvent(tarsqidoc=self.tarsqidoc)

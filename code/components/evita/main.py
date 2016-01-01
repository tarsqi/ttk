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
        """Set the NAME instance variable. The xmldoc and doctree variables are
        filled in during processing."""
        self.NAME = EVITA
        self.xmldoc = None
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


# TODO: the following code is obsolete, but parts of it may be useful and could
# be added to TarsqiDocElement

def  _create_xml_string(element):
    """Creates an XML string with <DOC>, <s>, <NG>, <VG> and <lex> tags. It does
    not include <TIMEX3> tags because those are currently not yet used by
    Evita. Strings look like this:

    <DOC>
    <s>
      <lex pos="NNP">John</lex>
      <VG>
        <lex pos="VBZ">sleeps</lex>
      </VG>
    </s>
    </DOC>

    Note that white space is not relevant. Also, this method will add NG tags,
    but it is not clear whether those are needed by Evita, at least, they are
    not needed for this particular example."""

    lexes = sorted(element.tarsqi_tags.find_tags('lex'))
    sentences = {s.begin : s for s in element.tarsqi_tags.find_tags('s')}
    vgs = {vg.begin : vg for vg in element.tarsqi_tags.find_tags('VG')}
    ngs = {ng.begin : ng for ng in element.tarsqi_tags.find_tags('NG')}
    xmlstring = StringIO.StringIO()
    xmlstring.write("<DOC>\n")
    stack = Stack()
    for lex in lexes:
        _write_open_s(lex, xmlstring, stack, sentences)
        _write_open_vg(lex, xmlstring, stack, vgs)
        _write_open_ng(lex, xmlstring, stack, ngs)
        # TODO: not sure whether the escape is needed here, check whether it
        # works out correctly with the offsets, something similar may need to be
        # checked in the gutime wrapper
        text = escape(element.doc.text(lex.begin, lex.end))
        xmlstring.write("%s%s\n" % (stack.indent*' ', lex.as_lex_xml_string(text)))
        _write_closing_tag(lex, stack.ng_end, 'NG', xmlstring, stack)
        _write_closing_tag(lex, stack.vg_end, 'VG', xmlstring, stack)
        _write_closing_tag(lex, stack.s_end, 's', xmlstring, stack)
    xmlstring.write("</DOC>\n")
    return xmlstring.getvalue()


def _write_open_s(lex, xmlstring, stack, sentences):
    if sentences.has_key(lex.begin):
        stack.s_end = sentences[lex.begin].end
        xmlstring.write("<s>\n")
        stack.indent += 2

def _write_open_ng(lex, xmlstring, stack, ngs):
    if ngs.has_key(lex.begin):
        stack.ng_end = ngs[lex.begin].end
        xmlstring.write("%s<NG>\n" % (stack.indent*' '))
        stack.indent += 2

def _write_open_vg(lex, xmlstring, stack, vgs):
    if vgs.has_key(lex.begin):
        stack.vg_end = vgs[lex.begin].end
        xmlstring.write("%s<VG>\n" % (stack.indent*' '))
        stack.indent += 2

def _write_closing_tag(lex, end, tag, xmlstring, stack):
    """Write a closing tag if the end for that tag is equal to the end of the lex."""
    # TODO: this is brittle and may only work for the built-in chunker
    if lex.end == end:
        stack.indent -= 2
        xmlstring.write("%s</%s>\n" % (stack.indent*' ', tag))


class Stack(object):
    """Auxiliary datastructure used by _create_xml_string(). Its main task is to
    track what the closing position is of a currently open s, NG or VG tag."""
    def __init__(self):
        self.s_end = None
        self.ng_end = None
        self.vg_end = None
        self.indent = 0

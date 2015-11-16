"""Main module for Evita, the event recognition component.

Responsible for the top-level processing of Evita.

"""

import StringIO
from xml.sax.saxutils import escape, quoteattr

from components.evita.gramChunk import getWordList, getPOSList
from components.common_modules.component import TarsqiComponent
from docmodel.xml_parser import Parser
from library.tarsqi_constants import EVITA
from utilities import logger
from utilities.converter import FragmentConverter


class Evita (TarsqiComponent):

    """Class that implements Evita's event recognizer. Instance variables: NAME: a string,
    doctree: a Document instance. """

    def __init__(self):
        """Set the NAME instance variable. The xmldoc and doctree variables are
        filled in during processing."""
        self.NAME = EVITA
        self.xmldoc = None
        self.doctree = None
        
    def process_file(self, infile, outfile):
        """Process a fragment file and write a file with EVENT tags. The two arguments are
        both absolute paths."""
        self.xmldoc = Parser().parse_file(open(infile,'r'))
        self.doctree = FragmentConverter(self.xmldoc, infile).convert()
        self.extractEvents()
        self.xmldoc.save_to_file(outfile)
        
    def process_xmldoc(self, xmldoc):
        """Process an XmlDocument fragment and return one with EVENT tags. Takes an
        instance of XmlDocument as its sole argument."""
        self.xmldoc = xmldoc
        self.doctree = FragmentConverter(self.xmldoc).convert()
        self.extractEvents()
        return self.xmldoc
        
    def process_string(self, xmlstring):
        """Process a fragment string and return a string with EVENT tags. Takes a string
        as its sole argument, throws an error if this string is not well-formed XML."""
        self.xmldoc = Parser().parse_string(xmlstring)
        self.doctree = FragmentConverter(self.xmldoc).convert()
        self.extractEvents()
        return self.xmldoc.toString()

    def process_element(self, element):
        """Process an instance of docmodel.document.TarsqiDocParagraph. Note
        that contrary to the other processing methods, in this case the xmldoc
        and doctree variables on the Evita instance are the ones for just one
        element and not for the whole document or string. Events are added to
        the tag repository on the element."""
        # TODO: instead of this maybe create a doctree directly
        xml_string = _create_xml_string(element)
        self.process_string(xml_string)
        _import_event_tags(self.xmldoc, element)
        #print xml_string
        #self.xmldoc.pp()
        #self.doctree.pp()
        #print self.xmldoc.toString()

    def extractEvents(self):
        """Loop through all sentences in self.doctree and through all nodes in each
        sentence and determine if the node contains an event."""
        for sentence in self.doctree:
            #sentence.pp(tree=False)
            logger.debug("SENTENCE: %s" % ' '.join(getWordList(sentence)))
            for node in sentence:
                #print node
                #node.pp()
                if not node.flagCheckedForEvents:
                    node.createEvent()
            #print; sentence.pp(tree=True)
        #self.doctree.pp()


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

def _import_event_tags(xmldoc, doc_element):
    """Find all the information for each event in the XmlDocument and add it to the
    document element. This involves merging information from the EVENT tag, the
    MAKEINSTANCE tag and the embedded lex tag (for the offsets)."""
    current_event = None
    xmlelement = xmldoc.elements[0]
    while xmlelement:
        if xmlelement.content.startswith('<EVENT'):
            current_event = xmlelement.attrs
        if xmlelement.content.startswith('<lex') and current_event:
            current_event['begin'] = xmlelement.attrs['begin']
            current_event['end'] = xmlelement.attrs['end']
        if xmlelement.content.startswith('<MAKEINSTANCE') and current_event:
            current_event.update(xmlelement.attrs)
            current_event = { k:v for k,v in current_event.items()
                              if v is not None and k is not 'eventID' }
            #print current_event
            begin = int(current_event.pop('begin'))
            end = int(current_event.pop('end'))
            doc_element.add_event(begin, end, current_event)
            current_event = None
        xmlelement = xmlelement.get_next()

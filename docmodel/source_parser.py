"""Source parsers for Toolkit input

Module that contains classes to parse and represent the input document. All
parsers have a parse_file() and a parse_string() method and these methods return
an instance of TarsqiDocument. Of that instance, all the parsers in this file do
is to instantiate the source instance variable, which contains an instance of
SourceDoc.

What parser is used is defined in main.py, which has a mapping form source types
(handed in by the --source command line option) to source parsers.

There are now three parsers:

SourceParserXML

   A simple XML parser that splits inline XML into a source string and a list of
   tags. The source string and the tags are stored in the SourceDoc instance,
   which is intended to provide just enough functionality to deal with the input
   in a read-only fashion, that is, additional annotations should not be in this
   instance.

SourceParserText

   Simply puts the entire text in the DocSource instance and leaves the
   TagsRepository empty.

SourceParserTTK

   This parser deals with the ttk format. In the TTK format there are two main
   sources for tags: source_tags and tarsqi_tags. The first are added to the
   tags repository on the SourceDoc (which is considered read-only after that),
   the second are added to the tags repository on the TarsqiDocument.

"""

import sys, codecs, pprint
import xml.parsers.expat
from xml.sax.saxutils import escape, quoteattr
from xml.dom import minidom

from docmodel.document import TarsqiDocument, SourceDoc
from docmodel.document import OpeningTag, ClosingTag


class SourceParser:

    DEBUG = False


class SourceParserText(SourceParser):

    def parse_file(self, filename, tarsqidoc):
        """Parses filename and returns a SourceDoc. Simply dumps the full file
        content into the text variable of the SourceDoc."""
        tarsqidoc.sourcedoc = SourceDoc(filename)
        tarsqidoc.sourcedoc.text = codecs.open(filename, encoding='utf8').read()

    def parse_string(self, text, tarsqidoc):
        """Parses a text string and returns a SourceDoc. Simply dumps the full
        string into the text variable of the SourceDoc."""
        tarsqidoc.sourcedoc = SourceDoc(None)
        # TODO: do we need to ensure the text is unicode?
        tarsqidoc.sourcedoc.text = text


class SourceParserTTK(SourceParser):

    def __init__(self):
        """Initialize the three variables dom, topnodes and sourcedoc."""
        self.dom = None
        self.topnodes = {}
        self.sourcedoc = None
        self.tarsqidoc = None

    def parse_file(self, filename, tarsqidoc):
        """Parse the TTK file and put the contents in the appropriate parts of
        the SourceDoc."""
        # TODO: does this do the right thing for non-ascii?
        self.dom = minidom.parse(open(filename))
        self._load_topnodes()
        self._parse(tarsqidoc)

    def parse_string(self, text, tarsqidoc):
        """Parse the TTK string and put the contents in the appropriate parts of the
        SourceDoc."""
        self.dom = minidom.parseString(text)
        self._load_topnodes()
        self._parse(tarsqidoc)

    def _load_topnodes(self):
        """Fills the topnodes dictionary with text, metadata, source_tags and
        tarsqi_tags and comment keys."""
        for node in self.dom.documentElement.childNodes:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                self.topnodes[node.tagName] = node

    def _parse(self, tarsqidoc):
        self.sourcedoc = SourceDoc(None)
        self.tarsqidoc = tarsqidoc
        self.tarsqidoc.sourcedoc = self.sourcedoc
        self.sourcedoc.text = self.topnodes['text'].firstChild.data
        self._add_source_tags()
        self._add_tarsqi_tags()
        self._add_comments()
        self._add_metadata()

    def _add_source_tags(self):
        """Add the source_tags in the TTK document to the tags repository
        on the SourceDoc."""
        for node in self.topnodes['source_tags'].childNodes:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                self._add_to_source_tags(node)

    def _add_tarsqi_tags(self):
        """Add the tarsqi_tags in the TTK document to the tags repository
        on the TarsqiDocument."""
        for node in self.topnodes['tarsqi_tags'].childNodes:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                self._add_to_tarsqi_tags(node)

    def _add_comments(self):
        # unlike the other top-level tags, comments are optional
        comments = self.topnodes.get('comments')
        if comments:
            for node in self.topnodes['comments'].childNodes:
                if node.nodeType == minidom.Node.ELEMENT_NODE:
                    offset = node.getAttribute('offset')
                    comment = node.firstChild.data
                    self.sourcedoc.comments[int(offset)] = [comment]

    def _add_metadata(self):
        for node in self.topnodes['metadata'].childNodes:
            if node.nodeType == minidom.Node.ELEMENT_NODE:
                self.sourcedoc.metadata[node.nodeName] = node.getAttribute('value')

    def _add_to_source_tags(self, node):
        tag_repository = self.sourcedoc.tags
        self._add_to_tag_repository(node, tag_repository)

    def _add_to_tarsqi_tags(self, node):
        tag_repository = self.tarsqidoc.tags
        self._add_to_tag_repository(node, tag_repository)

    def _add_to_tag_repository(self, node, tag_repository):
        name = node.tagName
        o1 = node.getAttribute('begin')
        o2 = node.getAttribute('end')
        o1 = int(o1) if o1 else -1
        o2 = int(o2) if o2 else -1
        attrs = dict(node.attributes.items())
        attrs = dict([(k, v) for (k, v) in attrs.items()
                      if k not in ('begin', 'end')])
        tag_repository.add_tag(name, o1, o2, attrs)


def print_dom(node, indent=0):
    if node is None:
        return
    if node.nodeType == minidom.Node.TEXT_NODE and not node.data.strip():
        return
    print "%s%s" % (indent * ' ', node)
    for childnode in node.childNodes:
        print_dom(childnode, indent + 3)


class SourceParserXML(SourceParser):

    """Simple XML parser, using the Expat parser.

    Instance variables
       encoding - a string
       sourcedoc - an instance of SourceDoc
       parser - an Expat parser """

    # TODO: may need to add other handlers for completeness, see
    # http://docs.python.org/library/pyexpat.html, note however that if we
    # change our notion of primary data than we may not need to do that.

    # TODO. The way this is set up now requires the SourceDoc to know a lot
    # about the internal workings of the Expat parser (for example the notion
    # that begin and end tags are found separately). It is probably better to
    # keep that knowledge here, by building lists of tags here and only export
    # them after all elements are gathered (see note in parse_file).

    def __init__(self, encoding='utf-8'):
        """Set up the Expat parser."""
        self.encoding = encoding
        self.sourcedoc = None
        self.parser = xml.parsers.expat.ParserCreate(encoding=encoding)
        self.parser.buffer_text = 1
        self.parser.XmlDeclHandler = self._handle_xmldecl
        self.parser.ProcessingInstructionHandler = \
            self._handle_processing_instruction
        self.parser.CommentHandler = self._handle_comment
        self.parser.StartElementHandler = self._handle_start
        self.parser.EndElementHandler = self._handle_end
        self.parser.CharacterDataHandler = self._handle_characters
        self.parser.DefaultHandler = self._handle_default

    def parse_file(self, filename, tarsqidoc):
        """Parses filename and returns a SourceDoc. Uses the ParseFile routine
        of the expat parser, where all the handlers are set up to fill in the
        text and tags in SourceDoc."""
        self.sourcedoc = SourceDoc(filename)
        # TODO: should this be codecs.open() for non-ascii?
        self.parser.ParseFile(open(filename))
        self.sourcedoc.finish()
        tarsqidoc.sourcedoc = self.sourcedoc

    def parse_string(self, text, tarsqidoc):
        """Parses a text string and returns a SourceDoc. Uses the ParseFile routine of
        the expat parser, where all the handlers are set up to fill in the text
        and tags in SourceDoc."""
        self.sourcedoc = SourceDoc(None)
        # TODO: do we need to make sure that text is unicode?
        self.parser.Parse(text)
        self.sourcedoc.finish()
        tarsqidoc.sourcedoc = self.sourcedoc

    def _handle_xmldecl(self, version, encoding, standalone):
        """Store the XML declaration."""
        self._debug('xmldec')
        self.sourcedoc.xmldecl = (version, encoding, standalone)

    def _handle_processing_instruction(self, target, data):
        """Store processing instructions"""
        self._debug('proc', target, len(data))
        self.sourcedoc.add_processing_instruction(target, data)

    def _handle_comment(self, data):
        """Store comments."""
        self._debug('comment', len(data))
        self.sourcedoc.add_comment(data)

    def _handle_start(self, name, attrs):
        """Handle opening tags. Takes two arguments: a tag name and a dictionary
        of attributes. Asks the SourceDoc instance in the sourcedoc variable to
        add an opening tag."""
        self._debug('start', name, attrs)
        #print ',,,', name, attrs
        self.sourcedoc.add_opening_tag(name, attrs)

    def _handle_end(self, name):
        """Add closing tags to the SourceDoc."""
        self._debug('end', name)
        self.sourcedoc.add_closing_tag(name)

    def _handle_characters(self, string):
        """Handle character data by asking the SourceDocument to add the
        data. This will not necesarily add a contiguous string of character data
        as one data element. This should include ingnorable whtespace, but see
        the comment in the method below, I apparently had reason to think
        otherwise."""
        self._debug('chars', len(string), string)
        self.sourcedoc.add_characters(string)

    def _handle_default(self, string):
        """Handle default data by asking the SourceDoc to add it as
        characters. This is here to get the 'ignoreable' whitespace, which I do
        not want to ignore."""
        # TODO: maybe ignore that whitespace after all, it does not seem to
        # matter though
        self._debug('default', len(string), string)
        self.sourcedoc.add_characters(string)

    def _debug(self, *rest):
        if SourceParser.DEBUG:
            p1 = "%s-%s" % (self.parser.CurrentLineNumber,
                            self.parser.CurrentColumnNumber)
            p2 = "%s" % self.parser.CurrentByteIndex
            print("%-5s  %-4s    %s" %
                  (p1, p2, "  ".join(["%-8s" % replace_newline(x) for x in rest])))


def replace_newline(text):
    """Just used for debugging, make sure to not use this elsewhere because it
    is dangerous since it turns unicode into non-unicode."""
    return str(text).replace("\n", '\\n')

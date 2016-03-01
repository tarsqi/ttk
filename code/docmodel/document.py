"""TarsqiDocument and friends.

This module contains TarsqiDocument and some of the classes used by it.

"""

import sys, codecs
from copy import copy
from xml.sax.saxutils import escape, quoteattr


class TarsqiDocument:

    """An instance of TarsqiDocument should contain all information that may be needed by
    the wrappers to do their work. It will contain minimal document structure in its
    elements variable, at this point just a list of TarsqiDocElements. Elements will be
    typed and include the source string and a dictionary of tags. 

    Instance Variables:
       source - instance of DocSource
       doctree - instance of TarsqiTree
       elements - list of TarsqiDocElements
       metadata - a dictionary
       options - the Options instance from the Tasqi instance
       counters - a set of counters used to create unique identifiers

    Note that more variables will be needed. Currently, several wrappers use data from
    the Tarsqi instance, should check what these data are and get them elsewhere,
    potentially by adding them here.

    Also note that he processing options are available to the wrappers only
    through this class by accessing th eoptions variable.

    Also note that we may need a tarsqi_tags variable, to store those tags that are not
    internal to any of the elements."""

    def __init__(self, docsource, metadata):
        self.source = docsource
        self.elements = []
        self.metadata = metadata
        self.options = {}
        self.counters = { 'TIMEX3': 0, 'EVENT': 0, 'ALINK': 0, 'SLINK': 0, 'TLINK': 0 }

    def __str__(self):
        return "<%s on '%s'>" % (self.__class__, self.source.filename)

    def add_options(self, options):
        self.options = options

    def get_dct(self):
        return self.metadata.get('dct')

    def text(self, p1, p2):
        return self.source.text[p1:p2]

    def pp(self, source=True, elements=True):
        print "\n", self, "\n"
        for key, value in self.metadata.items():
            print "   metadata.%-17s  -->  %s" % (key, value)
        for key, value in self.options.items():
            print "   options.%-15s  -->  %s" % (key, value)
        if source:
            self.source.pp()
        if elements:
            for e in self.elements: e.pp()

    def next_event_id(self):
        self.counters['EVENT'] += 1
        return "e%d" % self.counters['EVENT']

    def next_timex_id(self):
        self.counters['TIMEX3'] += 1
        return "t%d" % self.counters['TIMEX3']

    def next_link_id(self, link_type):
        """Return a unique lid. The link_type argument is one of {ALINK,SLINK,TLINK} and
         determines what link counter is incremented. The lid itself is the sum
         of all the link counts. Assumes that all links are added using the link
         counters in the document. Breaks down if there are already links added
         without using those counters."""
        self.counters[link_type] += 1
        return "l%d" % (self.counters['ALINK']
                        + self.counters['SLINK']
                        + self.counters['TLINK'])

    def print_source(self, fname):
        """Print the original source of the document, without the tags to file fname."""
        self.source.print_source(fname)

    def print_sentences(self, fname=None):
        """Write to file (or stadard output if no filename was given) a Python variable
        assignment where the content of the variable the list of sentences as a list of
        lists of token strings."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("sentences = ")
        fh.write(str(self.list_of_sentences()))
        fh.write("\n")

    def print_all(self, fname):
        """Write source string, source tags and ttk tags all to one file."""
        fh = codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("<ttk>\n")
        fh.write("<text>%s</text>\n" % escape(self.source.text))
        if self.source.comments:
            fh.write("<comments>\n")
            for offset in sorted(self.source.comments.keys()):
                for comment in self.source.comments[offset]:
                    comment = escape(comment.replace("\n", '\\n'))
                    fh.write("  <comment offset=\"%s\">%s</comment>\n" % (offset, comment))
            fh.write("</comments>\n")
        fh.write("<source_tags>\n")
        for tag in self.source.source_tags.tags:
            fh.write("  %s\n" % tag.as_ttk_tag())
        fh.write("</source_tags>\n")
        fh.write("<ttk_tags>\n")
        fh.write("  <TIMEX3 tid=\"t0\" type=\"DATE\" value=\"%s\"" % self.metadata['dct']
                 + " functionInDocument=\"CREATION_TIME\"/>\n")
        for e in self.elements:
            fh.write("  <doc_element type=\"%s\" begin=\"%s\" end=\"%s\">\n"
                     % (e.__class__.__name__, e.begin, e.end))
            for tag in sorted(e.tarsqi_tags.tags):
                fh.write("    %s\n" % tag.as_ttk_tag())
            fh.write("  </doc_element>\n")
        fh.write("</ttk_tags>\n")
        fh.write("</ttk>\n")

    def print_source_tags(self, fname=None):
        """Prints all the tags from the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        for tag in self.source.source_tags.tags:
            fh.write(tag.as_ttk_tag()+"\n")

    def print_tarsqi_tags(self, fname=None):
        """Prints all the tarsqi tags added to the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("<ttk>\n")
        for e in self.elements:
            for tag in e.tarsqi_tags.tags:
                fh.write('  ' + tag.as_ttk_tag() + "\n")
        fh.write("</ttk>\n")

    def _print_tags(self, tag_repository, fname=None):
        """Prints all the tarsqi tags added to the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        for e in self.elements:
            for tag in tag_repository.source_tags:
                fh.write(tag.as_ttk_tag()+"\n")

    def list_of_sentences(self):
        sentences = []
        sentence = []
        for element in self.elements:
            for t in element.tarsqi_tags.tags:
                if t.name == 's':
                    if sentence:
                        sentences.append(sentence)
                        sentence = []
                elif t.name == 'lex':
                    sentence.append(self.text(t.begin, t.end))
            if sentence:
                sentences.append(sentence)
            sentence = []
        return sentences
        

            
class TarsqiDocElement:
    """Contains a slice from a TarsqiDocument. The slice is determined by the begin
    and end instance variables and the content of text is the slice from the
    source document. The slice includes the tags that are relevant to this
    element. These tags have offsets that are relative to the entire document,
    these can be translated into local offsets using self.begin."""

    ELEMENT_ID = 0
    
    def __init__(self, tarsqidoc, begin, end):
        self._assign_identifier()
        self.doc = tarsqidoc
        self.begin = begin
        self.end = end
        self.source_tags = TagRepository()
        self.tarsqi_tags = TagRepository()

    def __str__(self):
        return "<%s #%d %d:%d>\n\n%s\n" % \
               (self.__class__, self.id, self.begin, self.end, 
                self.get_text().encode('utf-8').strip())
            
    def _assign_identifier(self):
        self.__class__.ELEMENT_ID += 1
        self.id = self.__class__.ELEMENT_ID

    def is_paragraph(): return False

    def get_text(self):
        """Return the text slice in this element."""
        return self.doc.text(self.begin, self.end)
    
    def add_source_tags(self, tag_repository):
        """Add all tags from a TagRepostitory (handed in from the SourceDoc) that fall
        within the scope of this element. Also includes tags whose begin is
        before and whose end is after the element. Makes a shallow copy of the
        Tag from the SourceDoc TagRepository."""
        # note that tag_repository is also available in self.doc.source.tags
        for t in tag_repository.tags:
            if (t.begin >= self.begin and t.end <= self.end) \
                    or (t.begin <= self.begin and t.end >= self.end):
                self.source_tags.append(copy(t))

    def add_timex(self, begin, end, attrs):
        """Add a TIMEX3 tag to the tarsqi_tags tag repository."""
        self.tarsqi_tags.add_tag('TIMEX3', begin, end, attrs)

    def add_event(self, begin, end, attrs):
        """Add an EVENT tag to the tarsqi_tags tag repository."""
        self.tarsqi_tags.add_tag('EVENT', begin, end, attrs)

    def has_event(self, begin, end):
        """Return True if there is already an event at the given begin and end."""
        for tag in self.tarsqi_tags.find_tags('EVENT'):
            if tag.begin == begin and tag.end == end:
                return True
        return False

    def pp(self):
        print "\n", self
        for tag in self.source_tags.tags:
            print "  source_tag  %s" % tag
        for tag in self.tarsqi_tags.tags:
            print "  tarsqi_tag  %s" % tag

    
class TarsqiDocParagraph(TarsqiDocElement):

    def __init__(self, begin, end, text):
        TarsqiDocElement.__init__(self, begin, end, text)

    def is_paragraph():
        return True



class SourceDoc:

    """A SourceDoc is created by a SourceParser and contains source data and
    annotations of those data. The source data are put in the text variable as a
    unicode string, tags are in the source_tags and tarsqi_tags variables and
    contain begin and end positions in the source."""

    def __init__(self, filename='<STRING>'):
        """Initialize a SourceDoc on a filename or a string."""
        self.filename = filename
        self.xmldecl = None
        # initialize as a list, will be a string later
        self.text = []
        self.comments = {}
        self.processing_instructions = {}
        self.source_tags = TagRepository()
        self.tarsqi_tags = TagRepository()
        self.offset = 0
        self.tag_number = 0

    def __getitem__(self, i):
        return self.text[i]

    def add_opening_tag(self, name, attrs):
        """Add an opening tag to source_tags. This is used by the StartElementHandler of
        the Expat parser in SourceParserXML."""
        #print self.offset
        self.tag_number += 1
        self.source_tags.add_tmp_tag( OpeningTag(self.tag_number, name, self.offset, attrs) )

    def add_closing_tag(self, name):
        """Add a closing tag  to source_tags. This is used by the EndElementHandler of
        the Expat parser in SourceParserXML."""
        #print self.offset
        self.tag_number += 1
        self.source_tags.add_tmp_tag( ClosingTag(self.tag_number, name, self.offset) )

    def add_characters(self, string):
        """Add a character string to the source and increment the current offset. Used
        by the CharacterDataHandler of the Expat parser in SourceParserXML."""
        #print 'adding', len(string), 'characters'
        self.text.append(string) # this is already unicode
        self.offset += len(string)

    def add_comment(self, string):
        self.comments.setdefault(self.offset,[]).append(string)

    def add_processing_instruction(self, target, data):
        self.processing_instructions.setdefault(self.offset,[]).append((target, data))

    def finish(self):
        """Transform the source list into a string, merge the begin and end tags, and
        index the tags on offsets."""
        # TODO: this is probably different depending on what source parser is used
        self.text = ''.join(self.text)
        self.source_tags.merge()
        self.source_tags.index()

    def pp(self):
        """Print source and tags."""
        print "\n<SourceDoc on '%s'>\n" % self.filename
        print self.text.encode('utf-8').strip()
        print "\nTAGS:"
        self.source_tags.pp()
        print "\nXMLDECL:", self.xmldecl
        print "COMMENTS:", self.comments
        print "PROCESSING:", self.processing_instructions

    def print_source(self, filename):
        """Print the source string to a file, using the utf-8 encoding."""
        fh = open(filename, 'w')
        fh.write(self.text.encode('utf-8'))

    def print_tags(self, filename):
        """Print all the tags to a file. Each tag is printed on a tab-separated line with
        opening offset, closing offset, tag name, and attribute value pairs."""
        fh = open(filename, 'w')
        for t in self.source_tags.tags:
            fh.write("%d\t%d\t%s" % (t.begin, t.end, t.name))
            for (attr, val) in t.attrs.items():
                fh.write("\t%s=\"%s\"" % (attr, val.replace('"','&quot;')))
            fh.write("\n")


    def print_xml(self, filename):

        """Print self as an inline XML file. This should work on all input that did
        not generate a warning while parsing. The output file is identical to
        the input file modulo processing instructions, comments, and the order
        of attributes in an opening tag and the kind of quotes used. Also, tags
        that were printed as <SOME_TAG/> will be printed as two tags. There are
        no provisions for crossing tags. Therefore, the code is also not set up
        to deal with tags added to the tags repository since those may have
        introduced crossing tags."""

        # TODO: check what happens when input is not an xml file
        # TODO: add xmldec, processing instructions and comments

        xml_string = u''  # TODO: use a string buffer
        offset = 0
        stack = []

        for char in self.text:

            # any tags on the stack that can be closed?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching:
                xml_string += "</%s>" % t.name

            # any new opening tags?
            for t in self.source_tags.opening_tags.get(offset,[]):
                stack.append(t)
                xml_string += "<%s%s>" % (t.name, t.attributes_as_string())

            # any of those need to be closed immediately (non-consuming tags)?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching:
                xml_string += "</%s>" % t.name

            xml_string += escape(char)
            offset += 1

        fh = open(filename, 'w')
        fh.write(xml_string.encode('utf-8'))


    def _matching_closing_tags(self, offset, stack, matching):
        """Recursively return the closing tags that match the tail of the stack of opening
        tags."""
        if not stack:
            return (stack, matching)
        last = stack[-1]
        if self.source_tags.closing_tags.get(offset,{}).get(last.begin,{}).get(last.name,False):
            stack.pop()
            matching.append(last)
            return self._matching_closing_tags(offset, stack, matching)
        else:
            return (stack, matching)



class TagRepository:

    """Class that provides access to the tags for a document. An instance of this class is
    used for the DocSource instance, other instances will be used for the elements in a
    TarsqiDocument. For now, the repository has the following structure:

    self.tmp
       A list of OpeningTag and ClosingTag elements, used only to build the tags list.

    self.tags
       A list with Tag instances.

    self.opening_tags
       A dictionary of tags indexed on begin offset, the values are lists of Tag
       instances, again ordered on id (thereby reflecting text order, but only
       for tags in the original input).

    self.closing_tags
       A dictionary indexed on end offset and begin offset, the values are dictionary of
       tagnames. For example, closing_tags[547][543] = {'lex':True, 'NG':True } indicates
       that there is both a lex tag and an NG tag from 543-547. The opening tags
       dictionary will have encoded that the opening NG occurs before the opening lex:
       opening_tags[543] = [<Tag 204 NG 543-547 {}>, <Tag 205 lex 543-547 {...}]

    """

    # TODO: the closing_tags dictionary is delusional in that it cannot deal
    # with multiple tags with the same name, begin and end. The question is
    # whether the opening and closing tags are needed, all they seem to do is be
    # there for when we create an XML document, which we may want to relegate to
    # another component alltogether.

    def __init__(self):
        self.tmp = []
        self.tags = []
        self.opening_tags = {}
        self.closing_tags = {}

    def all_tags(self):
        return self.tags

    def add_tmp_tag(self, tagInstance):
        """Add a OpeningTag or ClosingTag to a temporary list. Used by the XML
        handlers."""
        self.tmp.append(tagInstance)

    def add_tag(self, name, begin, end, attrs):
        """Add a tag to the tags list and the opening_tags and closing_tags
        dictionaries."""
        tag = Tag(None, name, begin, end, attrs)
        self.tags.append(tag)
        self.opening_tags.setdefault(begin,[]).append(tag)
        self.closing_tags.setdefault(end,{}).setdefault(begin,{})[tag.name] = True

    def append(self, tag):
        """Appends an instance of Tag to the tags list."""
        self.tags.append(tag)

    def merge(self):
        """Take the OpeningTags and ClosingTags in self.tmp and merge them into
        Tags. Raise errors if tags do not match."""
        stack = []
        for t in self.tmp:
            if t.is_opening_tag():
                stack.append(t)
            elif t.name == stack[-1].name:
                t1 = stack.pop()
                self.tags.append(Tag( t1.id, t1.name, t1.begin, t.end, t1.attrs ))
            else:
                raise TarsqiInputError("non-matching tag %s" % t)
        if stack:
            raise TarsqiInputError("no closing tag for %s" % stack[-1])
        self.tags.sort()

    def index(self):
        """Index tags on position."""
        self.opening_tags = {}
        self.closing_tags = {}
        for tag in self.tags:
            self.opening_tags.setdefault(tag.begin,[]).append(tag)
            self.closing_tags.setdefault(tag.end,{}).setdefault(tag.begin,{})[tag.name] = True
        for (k,v) in self.opening_tags.items():
            self.opening_tags[k].sort()

    def find_tags(self, name):
        """Return all tags of this name."""
        return [t for t in self.tags if t.name == name]

    def find_tag(self, name):
        """Return the first Tag object with name=name, return None if no such tag
        exists."""
        for t in self.tags:
            if t.name == name:
                return t
        return None

    def pp(self):
        self.pp_tags(indent='    ')
        #print; self.pp_opening_tags()
        #print; self.pp_closing_tags()

    def pp_tags(self, indent=''):
        for tag in self.tags: print "%s%s" % (indent, tag)

    def pp_opening_tags(self):
        print '<TagRepository>.opening_tags'
        for offset, list in sorted(self.opening_tags.items()):
            print "  %5d " % offset, "\n         ".join([x.__str__() for x in list])

    def pp_closing_tags(self):
        print '<TagRepository>.closing_tags'
        for offset, dict in sorted(self.closing_tags.items()):
            print "  %5d " % offset, dict


class Tag:

    """A Tag has a name, an id, a begin offset, an end offset and a dictionary
    of attributes. The id is handed in by the code that creates the Tag which
    could be: (1) the code that parses the source document, in which case
    identifiers are numbered depending on text position, (2) the preprocessor
    code, which assigns identifiers for lex, ng, vg and s tags, or (3) one of
    the components that creates tarsqi tags, in which case the identifier is
    None because special identifiers like eid, eiid, tid and lid are used."""

    def __init__(self, identifier, name, o1, o2, attrs):
        """Initialize id, name, begin, end and attrs instance variables."""
        self.id = identifier
        self.name = name
        self.begin = o1
        self.end = o2
        self.attrs = attrs

    def __str__(self):
        attrs = ''.join([" %s='%s'" % (k,v) for k,v in self.attrs.items()])
        return "<Tag %s id=%s %s:%s {%s }>" % \
               (self.name, self.id, self.begin, self.end, attrs)

    def __cmp__(self, other):
        """Order two Tags based on their begin offset and end offsets. Tags with an
        earlier begin will be ranked before tags with a later begin, with equal
        begins the tag with the higher end will be ranked first. Tags with no
        begin (that is, it is set to -1) will be ordered at the end. The order of
        two tags with the same begin and end is undefined."""
        if self.begin == -1: return 1
        if other.begin == -1: return -1
        begin_cmp = cmp(self.begin, other.begin)
        end_cmp =  cmp(other.end, self.end)
        return end_cmp if begin_cmp == 0 else begin_cmp

    def is_opening_tag(self): return False

    def is_closing_tag(self): return False

    def as_ttk_tag(self):
        """Return the tag as a tag in the Tarsqi output format."""
        begin = " begin=\"%s\"" % self.begin if self.begin >= 0 else ''
        end = " end=\"%s\"" % self.end if self.end >= 0 else ''
        identifier = "" if self.id is None else " id=" + quoteattr(str(self.id))
        return "<%s%s%s%s%s />" % \
            (self.name, identifier, begin, end, self.attributes_as_string())

    def as_lex_xml_string(self, text):
        return "<lex id=\"%s\" begin=\"%d\" end=\"%d\" pos=\"%s\">%s</lex>" % \
            (self.id, self.begin, self.end, str(self.attrs['pos']), escape(text))

    def attributes_as_string(self):
        """Return a string representation of the attributes dictionary."""
        if not self.attrs:
            return ''
        return ' ' + ' '.join(["%s=%s" % (k,quoteattr(v)) for (k,v) in self.attrs.items()])


class OpeningTag(Tag):

    "Like Tag, but self.end is always None."""

    def __init__(self, id, name, offset, attrs):
        Tag.__init__(self, id, name, offset, None, attrs)

    def __str__(self):
        return "<OpeningTag %d %s %d %s>" % \
            (self.id, self.name, self.begin, str(self.attrs))

    def is_opening_tag(self):
        return True


class ClosingTag(Tag):

    "Like Tag, but self.begin and self.attrs are always None."""
    
    def __init__(self, id, name, offset):
        Tag.__init__(self, id, name, None, offset, None)

    def __str__(self):
        return "<ClosingTag %d %s %d>" % \
            (self.id, self.name, self.end)

    def is_closing_tag(self):
        return True


class TarsqiInputError(Exception):
    pass


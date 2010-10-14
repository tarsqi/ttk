"""

Parser for Toolkit input

Module that contains classes to parse and represent the input document. It contains a
simple XML parser that splits inline XML into a source string and a list of tags. The
source string and the tags are stored in a SourceDoc instance, which is intended to
provide just enough functionailty to deal with the input in a read-only fashion, that is,
additional annotations should not be in this instance.

This class will likely be embedded in a Document instance or a DocumentModel instance. 

Classes:

    SourceParser
    SourceDoc
    TagRepository
    Tag
       OpeningTag
       ClosingTag
    TarsqiInputError
    
TODO: we now assume that the input is valid XML and has at least a root, should change
this and make a distinction between XML and non-XML, which will simply be treated by
adding the entire file content to DocSource.source while leaving DocSource.tags
empty. Implement this by adding ExPat error trapping to SourceParser.parse_file().

"""

import sys
import xml.parsers.expat
import xml.sax.saxutils
import pprint


class SourceParser:

    """Simple XML parser, using the Expat parser. 

    Instance variables
       doc - an XmlDocument
       parser - an Expat parser """

    # TODO: ad other handlers
    # SEE: http://docs.python.org/library/pyexpat.html

    
    def __init__(self, encoding='utf-8'):
        """Set up the Expat parser."""
        self.encoding = encoding
        self.parser = xml.parsers.expat.ParserCreate(encoding=encoding)
        self.parser.buffer_text = 1
        self.parser.XmlDeclHandler = self._handle_xmldecl
        self.parser.ProcessingInstructionHandler = self._handle_processing_instruction
        self.parser.CommentHandler = self._handle_comment
        self.parser.StartElementHandler = self._handle_start
        self.parser.EndElementHandler = self._handle_end
        self.parser.CharacterDataHandler = self._handle_characters
        self.parser.DefaultHandler = self._handle_default
        
    def parse_file(self, filename):
        file = open(filename)
        """Parse a file, forwards to the ParseFile routine of the expat parser. Takes a
        file object as its single argument and returns the SourceDoc. """
        self.sourcedoc = SourceDoc(filename)
        self.parser.ParseFile(file)
        self.sourcedoc.finish()
        return self.sourcedoc
    
    def parse_string(self, string):
        """Parse a string, forwards to the Parse routine of the expat parser. Takes a
        string as its single argument and returns the value of the doc variable. """
        self.parser.Parse(string)
        return self.doc

    def _handle_xmldecl(self, version, encoding, standalone):
        """Store the XML declaration."""
        self.sourcedoc.xmldecl = (version, encoding, standalone)

    def _handle_processing_instruction(self, target, data):
        """Store processing instructions"""
        self.sourcedoc.add_processing_instruction(target, data)

    def _handle_comment(self, data):
        """Store comments."""
        self.sourcedoc.add_comment(data)
        
    def _handle_start(self, name, attrs):
        """Handle opening tags. Takes two arguments: a tag name and a dictionary of
        attributes. Asks the SourceDoc instance in the sourcedoc variable to add an
        opening tag."""
        self.sourcedoc.add_opening_tag(name, attrs)
        
    def _handle_end(self, name):
        """Add closing tags to the SourceDoc."""
        self.sourcedoc.add_closing_tag(name)
        
    def _handle_characters(self, string):
        """Handle character data by asking the SourceDocument to add the data. This will
        not necesarily add a contiguous string of character data as one data element."""
        self.sourcedoc.add_characters(string)
               
    def _handle_default(self, string):
        """Handle default data by asking the SourceDoc to add it as characters. This is
        here to get the 'ignoreable whitespace, which I do not want to ignore."""
        self.sourcedoc.add_characters(string)


        
class SourceDoc:

    """A SourceDoc is created by the SourceParser and contains source data and annotations
    of those data. The source data are put in the source variable as a unicode string,
    tags are in the tags variable and contain begin and end positions in the source."""

    def __init__(self, filename='<STRING>'):
        """Initialize a SourceDoc on a filename or a string."""
        self.filename = filename
        self.xmldecl = None
        self.source = []
        self.comments = {}
        self.processing_instructions = {}
        self.tags = TagRepository()
        self.offset = 0
        self.tag_number = 0
        
    def add_opening_tag(self, name, attrs):
        """Add an opening tag."""
        self.tag_number += 1
        self.tags.add_tmp_tag( OpeningTag(self.tag_number, name, self.offset, attrs) )

    def add_closing_tag(self, name):
        """Add a closing tag."""
        self.tag_number += 1
        self.tags.add_tmp_tag( ClosingTag(self.tag_number, name, self.offset) )
        
    def add_characters(self, string):
        """Add a character string to the source and increment the current offset."""
        self.source.append(string) # this is already unicode
        self.offset += len(string)        

    def add_comment(self, string):
        self.comments.setdefault(self.offset,[]).append(string)
        
    def add_processing_instruction(self, target, data):
        self.processing_instructions.setdefault(self.offset,[]).append((target, data))

    def finish(self):
        """Transform the source list into a string, merge the begin and end tags, and
        index the tags on offsets."""
        self.source = ''.join(self.source)
        self.tags.merge()
        self.tags.index()

    def pp(self):
        """Print source and tags."""
        print '-' * 80
        print "<SourceDoc on '%s'>" % self.filename
        print '-' * 80
        print self.source.encode('utf-8')
        print '-' * 80
        for t in self.tags: print t
        print '-' * 80, "\n"

    def pp_opening(self):
        """Pretty print self.opening_tags."""
        print "OPENING:"
        offsets = self.opening_tags.keys()
        offsets.sort()
        for offset in offsets:
            print '  ', offset, '=>'
            for tag in self.opening_tags[offset]:
                print '   ', tag
        print
        
    def pp_closing(self):
        """Pretty print self.closing_tags."""
        pp = pprint.PrettyPrinter(indent=3)
        pp.pprint(self.closing_tags)
        print
        
        
    def print_xml(self, filename):

        """Print self as an inline XML file. This should work on all input that did not
        generate a warning while parsing. The output file is identical to the input file
        modulo the order of attributes in an opening tag and the kind of quotes
        used. Also, tags that were printed as <SOME_TAG/> will be printed as two
        tags. There are no provisions for crossing tags. Therefore, the code is also not
        set up to deal with tags added to the tags repository since those may have
        introduced crossing tags."""

        # TODO: add xmldec, processing instructions and comments
        
        xml_string = u''
        offset = 0
        stack = []
        
        for char in self.source:

            # any tags on the stack that can be closed?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching: 
                xml_string += "</%s>" % t.name

            # any new opening tags?
            for t in self.opening_tags.get(offset,[]):
                stack.append(t)
                xml_string += "<%s%s>" % (t.name, t.attributes_as_string())

            # any of those need to be closed immediately (non-consuming tags)?
            (stack, matching) = self._matching_closing_tags(offset, stack, [])
            for t in matching: 
                xml_string += "</%s>" % t.name

            xml_string += xml.sax.saxutils.escape(char)
            offset += 1

        fh = open(filename, 'w')
        fh.write(xml_string.encode('utf-8'))


    def _matching_closing_tags(self, offset, stack, matching):

        """Recursively return the closing tags that match the tail of the stack of opening
        tags."""
        
        if not stack:
            return (stack, matching)

        last = stack[-1]
        if self.closing_tags.get(offset,{}).get(last.begin,{}).get(last.name,False):
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
       A list with tags, ordered on id.

    self.opening_tags
       A dictionary of tags indexed on begin offset, the values are lists of Tag
       instances, again ordered on id (thereby reflecting text order).
    
    self.closing_tags
       A dictionary indexed on end offset and begin offset, the values are dictionary of
       tagnames. For example, closing_tags[547][543] = {'lex':True, 'NG':True } indicates
       that there is both a lex tag and an NG tag from 543-547. The opening tags
       dictionary will have encoded that the opening NG occurs before the opening lex:
       opening_tags[543] = [<Tag 204 NG 543-547 {}>, <Tag 205 lex 543-547 {...}]
       
    """
    
    def __init__(self):
        self.tmp = []
        self.tags = []
        self.opening_tags = {}
        self.closing_tags = {}

    def add_tmp_tag(self, tagInstance):
        """Add a OpeningTag or ClosingTag to a temporary list. Used by the XML
        handlers."""
        self.tmp.append(tagInstance)

    def add_tag(self, tag_specification):
        (name, begin, end, attrs) = tag_specification
        tag = Tag(None, name, begin, end, attrs)
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
        for tag in self.tags:
            self.opening_tags.setdefault(tag.begin,[]).append(tag)
            self.closing_tags.setdefault(tag.end,{}).setdefault(tag.begin,{})[tag.name] = True
        for (k,v) in self.opening_tags.items():
            self.opening_tags[k].sort()

    def find_tag(self, name):
        """Return the first Tag object with name=name, return None if no such tag
        exists."""
        for t in self.tags:
            if t.name == 'TEXT':
                return t
        return None

    def pp(self):
        print 'ALL TAGS:'
        self.print_tags(indent='  ')
        self.print_opening_tags()
        #self.print_closing_tags()
        
    def print_tags(self, indent=''):
        for tag in self.tags: print "%s%s" % (indent, tag)
    
    def print_opening_tags(self):
        for offset, list in sorted(self.opening_tags.items()):
            print offset
            for t in list: print '  ', t
        
    def print_closing_tags(self):
        for offset, list in sorted(self.closing_tags.items()):
            print offset
            for offset2, list2 in list.items(): print '  ', offset2, list2
        
        
        
class Tag:

    """A Tag has a name, an id, a begin offset, an end offset and a dictionary of
    attributes. Identifiers are created in two ways. When a tag is generated from the XML
    parsers, the id is generated as the text is parsed, so tags that occur earlier in the
    text have a lower id. This is the case for the tags that are in the input
    document. Tags that are added by Tarsqi processing receive an id by incrementing the
    IDENTIFIER class variable while looping through the XmlDocument. With this, we loose
    the nice property that tag ids reflect text order (although this would still be the
    case the first time Tags are added from the XmlDocument, but there may be several
    passes)."""
    
    IDENTIFIER = 0
    
    def __init__(self, id, name, o1, o2, attrs):
        """Initialize id, name, begin, end and attrs instance variables."""
        if id is None:
            Tag.IDENTIFIER += 1
            id = Tag.IDENTIFIER
        self.id = id
        self.name = name
        self.begin = o1
        self.end = o2
        self.attrs = attrs
        
    def __str__(self):
        return "<Tag %s %s %d-%d %s>" % \
               (self.id, self.name, self.begin, self.end, str(self.attrs))

    def __cmp__(self, other):
        """Order two Tags based on their id. The id is based on the text position of the
        opening tag. This guarantees that with tags that span the same tags (as for
        example with '<event><lex>party</lex></event>'), the embedding tag will come
        before the embedded tag."""
        return cmp(self.id, other.id)
        
    def is_opening_tag(self): return False

    def is_closing_tag(self): return False
    
    def attributes_as_string(self):
        """Return a string representation of the attributes dictionary."""
        if not self.attrs:
            return ''
        return ' ' + ' '.join(["%s=\"%s\"" % (k,v) for (k,v) in self.attrs.items()])


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


                 
class TarsqiInputError(Exception): pass


        
if __name__ == '__main__':
    
    IN = sys.argv[1]
    OUT = sys.argv[2]
    doc = SourceParser().parse_file(IN)
    doc.pp()
    doc.print_xml(OUT)

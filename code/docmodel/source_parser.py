"""

Parser for Toolkit input

Module that contains classes to parse and represent the document being processed by the
toolkit. It contains a simple XML parser that splits inline XML into a source string and a
list of tags. The source string and the tags are stored in an SourceDoc instance, which is
intended to provide just enough functionailty to deal with the input in a read-only
fashion, that is, additional annotations should not be in this instance.

This class will likely be embedded in a Document instance or a DocumentModel instance. 

TODO: we know assume that the input is valid XML and has at least a root, should change
this and make a distinction between XML and non-XML, which will simply be treated by
adding the entire file content to DocSource.source while leaving DocSource.tags empty.

"""

import sys
import xml.parsers.expat
import pprint


class Parser:

    """Simple XML parser, using the Expat parser. 

    Instance variables
       doc - an XmlDocument
       parser - an Expat parser """


    def __init__(self, encoding='utf-8'):

        """Set up the Expat parser."""

        self.encoding = encoding
        self.parser = xml.parsers.expat.ParserCreate(encoding=encoding)
        self.parser.buffer_text = 1
        self.parser.StartElementHandler = self._handle_start
        self.parser.EndElementHandler = self._handle_end
        self.parser.CharacterDataHandler = self._handle_characters
        self.parser.DefaultHandler = self._handle_default
        
        
    def parse_file(self, file):

        """Parse a file, forwards to the ParseFile routine of the expat parser. Takes a
        file object as its single argument and returns the SourceDoc. """

        self.sourcedoc = SourceDoc(file.name)
        self.parser.ParseFile(file)
        self.sourcedoc.finish()
        return self.sourcedoc
    
    
    def parse_string(self, string):

        """Parse a string, forwards to the Parse routine of the expat parser. Takes a
        string as its single argument and returns the value of the doc variable. """

        self.parser.Parse(string)
        return self.doc

    
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

        """Handle default data by asking the SourceDoc to add it as characters."""

        self.sourcedoc.add_characters(string)
        
        

        
class SourceDoc:

    """A SourceDoc contains source data and annotations thereon. It is the result of
    splitting an XML document into the annotated data and the tags. The source data are
    put in the source variable as a unicode string, tags are in the tags variable and
    contain begin and end positions in the source."""

    def __init__(self, filename='<STRING>'):

        """Initialize a SourceDoc on a filename or a string."""

        self.filename = filename
        self.source = []
        self.tags = []
        self.opening_tags = {}
        self.closing_tags = {}
        self.offset = 0
        self.tag_number = 0
        
        
    def add_opening_tag(self, name, attrs):

        """Add an opening tag."""

        self.tag_number += 1
        self.tags.append( ('OPEN', self.tag_number, name, self.offset, attrs) )

        
    def add_closing_tag(self, name):

        """Add a closing tag."""

        self.tag_number += 1
        self.tags.append( ('CLOSE', self.tag_number, name, self.offset) )

        
    def add_characters(self, string):

        """Add a character string to the source and increment the current offset."""

        self.source.append(string) # this is already unicode
        self.offset += len(string)        


    def finish(self):

        """Transform the source list into a string and merge the begin and end tags. Print
        warnings if tags do not match. Also populate opening_tags and closing_tags."""
        
        self.source = ''.join(self.source)

        stack = []
        merged_tags = []
        for t in self.tags:
            if t[0] == 'OPEN':
                stack.append(t)
            elif t[2] == stack[-1][2]:
                t1 = stack.pop()
                # Tag requires id, name, begin offset, end offset and attributes
                merged_tag = Tag( t1[1], t1[2], t1[3], t[3], t1[4] )
                merged_tags.append(merged_tag)
            else:
                raise TarsqiInputError("non-matching tag %s" % t)
        if stack:
            raise TarsqiInputError("no closing tag for %s" % stack[-1])

        merged_tags.sort()
        self.tags = merged_tags

        for tag in self.tags:
            self.opening_tags.setdefault(tag.begin,[]).append(tag)
            self.closing_tags.setdefault(tag.end,{}).setdefault(tag.begin,{})[tag.name] = True
        for (k,v) in self.opening_tags.items():
            self.opening_tags[k].sort()
            


    def pp(self):

        """Print source and tags."""

        print '-' * 80
        print "<SourceDoc on '%s'>" % self.filename
        print '-' * 80
        print self.source
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
                
            xml_string += char
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
            
        
        
        
class Tag:

    """A Tag has a name, an id, a begin offset, an end offset and a dictionary of
    attributes. The id is a number generated when the text was parsed, so tags that occur
    earlier in the text have a lower id."""
    
    def __init__(self, id, name, o1, o2, attrs):

        """Initialize id, name, begin, end and attrs instance variables."""
        
        self.id = id
        self.name = name
        self.begin = o1
        self.end = o2
        self.attrs = attrs
        

    def __str__(self):

        return "<Tag %d %s %d %d %s>" % \
               (self.id, self.name, self.begin, self.end, str(self.attrs))
    

    def __cmp__(self, other):

        """Order two Tags based on their id. The id is based on the text position of the
        opening tag."""

        return cmp(self.id, other.id)

        
    def attributes_as_string(self):

        """Return a string representation of the attributes dictionary."""

        return ' ' + ' '.join(["%s=\"%s\"" % (k,v) for (k,v) in self.attrs.items()])



class TarsqiInputError(Exception): pass



        
if __name__ == '__main__':
    
    IN = sys.argv[1]
    OUT = sys.argv[2]
    doc = Parser().parse_file(open(IN))
    doc.pp()
    doc.print_xml(OUT)

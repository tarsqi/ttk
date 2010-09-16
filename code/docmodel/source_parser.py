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

TODO: the tags variable on SourceDoc is simply a list, may need to be enhanced.

"""

import sys
import xml.parsers.expat



class Parser:

    """Implements the XML parser, using the Expat parser. 

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

        
    def add_opening_tag(self, name, attrs):

        """Add an opening tag."""

        self.opening_tags.setdefault(self.offset, []).append((name, attrs))
        self.tags.append( ('OPEN', name, attrs, self.offset) )

        
    def add_closing_tag(self, name):

        """Add a closing tag."""

        self.closing_tags.setdefault(self.offset, []).append((name,))
        self.tags.append( ('CLOSE', name, self.offset) )

        
    def add_characters(self, string):

        """Add a character string to the source and increment the current offset."""

        self.source.append(string) # this is already unicode
        self.offset += len(string)        


    def finish(self):

        """Transform the source list into a string and merge the begin and end
        tags. Print warnings if tags do not match."""
        
        self.source = ''.join(self.source)

        stack = []
        merged_tags = []
        for t in self.tags:
            if t[0] == 'OPEN':
                stack.append(t)
            elif t[1] == stack[-1][1]:
                t1 = stack.pop()
                merged_tags.append( (t1[3], t[2], t1[1], t1[2]) )
            else:
                raise tarsqiInputError("non-matching tag %s" % t)
        if stack:
            raise tarsqiInputError("no closing tag for %s" % stack[-1])

        merged_tags.sort()
        self.tags = merged_tags


    def pretty_print(self):

        """Print source and tags."""

        print '-' * 80
        print "<SourceDoc on '%s'>" % self.filename
        print '-' * 80
        print self.source
        print '-' * 80
        for t in self.tags:
            print "%-4d  %-4d  %-10s  %s" % t
        print '-' * 80
        print "\n\n"
        

    def print_xml(self, filename):

        """Print self as an inline XML file. This should work on all input that did not
        generate a warning while parsing. The output file is identical to the input file
        modulo the order of attributes in an opening tag and the kind of quotes
        used. There are no provisions for crossing tags. It is also not set up to deal
        with tags added to the tags repository."""

        def matching_closing_tags(stack, closing_tags):
            stack_copy = list(stack)
            answer = []
            while stack_copy:
                last_opened = stack_copy.pop()
                print '  last', last_opened
                for t in closing_tags:
                    if t[0] == last_opened[0]:
                        answer.append(t)
                        closing_tags.remove(t)
                        continue
            return answer
        
        xml_string = u''
        offset = 0
        stack = []
        for char in self.source:
            opening_tags = self.opening_tags.get(offset,[])
            closing_tags = self.closing_tags.get(offset,[])
            print '>>', stack
            print '    ', opening_tags, closing_tags
            matching_closing_tags(stack, closing_tags)
            for t in closing_tags:
                stack.pop()
                xml_string += "</%s>" % t[0]
            for t in opening_tags:
                stack.append(t)
                attrs = attributes_as_string(t[1])
                xml_string += "<%s%s>" % (t[0], attrs)
            xml_string += char
            offset += 1
        #print xml_string
        fh = open(filename, 'w')
        fh.write(xml_string.encode('utf-8'))



def attributes_as_string(attrs):

    """Takes a dictionary of attributes and returns a string representation of it."""

    tagstr = ''
    for key in attrs.keys():
        tagstr = tagstr + ' ' + key + '="' + attrs[key] + '"'
    return tagstr



class TarsqiInputError(Exception): pass



        
if __name__ == '__main__':
    
    IN = sys.argv[1]
    OUT = sys.argv[2]
    doc = Parser().parse_file(open(IN))
    #doc.pretty_print()
    doc.print_xml(OUT)

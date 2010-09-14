"""Simple XML parser

Contains a simple XML parser and classes that implement the parsed
data structures. The XML parser takes an XML document and creates an
instance of XmlDocument which contains a linked list of all XML
elements (concentrating on opening tags, closing tags, and character
data).

"""

import sys
import xml.parsers.expat
from components.common_modules.document import protectNode


# variable used for assigning unique IDs to XmlDocElements
elementID = 0


class Parser:

    """Implements the XML parser, using the Expat parser. 

    Instance variables
       doc - an XmlDocument
       parser - an Expat parser """


    def __init__(self, encoding='utf-8'):

        """Sets the doc variable to an empty XmlDocument and sets up the Expat parser."""

        self.doc = XmlDocument()
        self.parser = xml.parsers.expat.ParserCreate(encoding=encoding)
        self.parser.buffer_text = 1
        self.parser.StartElementHandler = self._handle_start
        self.parser.EndElementHandler = self._handle_end
        self.parser.CharacterDataHandler = self._handle_characters
        self.parser.DefaultHandler = self._handle_default

        self.encoding = encoding

        
        
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

        """Handle opening tags. Takes two arguments: a tag name and a
        dictionary of attributes. Asks the XmlDocument in the doc
        variable to add an opening element."""

        print self.parser.CurrentByteIndex, "<%s>" % name 
        tagstring = '<' + name + self._attributes(attrs) + '>'
        self.doc.add_opening_tag_element(name, attrs, tagstring)

        #self.tags.append( ('OPEN', name, attrs, self.offset) )
        self.sourcedoc.add_opening_tag(name, attrs)

        
    def _handle_end(self, name):

        """Handle closing tags by asking the XmlDocument to add it. Takes the
        tag name as the argument."""

        print self.parser.CurrentByteIndex, "<%s/>" % name
        self.doc.add_closing_tag_element(name, "</" + name + ">")

        #self.tags.append( ('CLOSE', name, self.offset) )
        self.sourcedoc.add_closing_tag(name)

        
    def _handle_characters(self, string):

        """Handles character data by asking the XmlDocument to add a data element. This
        will not necesarily add a contiguous string of character data as one data
        element. Takes the character string as the argument."""

        print self.parser.CurrentByteIndex, string
        self.doc.add_data_element(string)

        self.sourcedoc.add_characters(string)
        #self.source.append(string) # this is already unicode
        #self.offset += len(string)
        
        
    def _handle_default(self, string):

        """Handles default data by asking the XmlDocument to add a default
        element. Takes a string as an argument."""

        print self.parser.CurrentByteIndex, string
        self.doc.add_default_element(string)

        self.sourcedoc.add_characters(string)
        #self.source.append(string) # this is already unicode
        #self.offset += len(string)
        
        
    def _attributes(self, attrs):

        """Takes a dictionary of attributes and returns a string
        representation of it."""

        tagstr = ''
        for key in attrs.keys():
            tagstr = tagstr + ' ' + key + '="' + attrs[key] + '"'
        return tagstr




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
        self.opening_tags[self.offset] = (name, attrs)
        self.tags.append( ('OPEN', name, attrs, self.offset) )
        
    def add_closing_tag(self, name):
        """Add an closing tag."""
        self.closing_tags[self.offset] = (name,)
        self.tags.append( ('CLOSE', name, self.offset) )

    def add_characters(self, string):
        """Add a character string to the source and increment the current offset."""
        self.source.append(string) # this is already unicode
        self.offset += len(string)        


    def finish(self):

        """Transform the source list into a string and merged the begin and end
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
                print "ERROR: non-matching tag %s" % t
        if stack:
            print "ERROR: no closing tag for %s" % stack[-1]

        merged_tags.sort()
        self.tags = merged_tags


    def pp(self):
        """Print source and tags."""
        print "<SourceDoc on '%s'>" % self.filename
        print self.source
        for t in self.tags:
            print "%-4d  %-4d  %-10s  %s" % t
                

    def print_xml(self):

        xml_string = u''
        offset = 0
        for char in self.source:
            opening_tag = self.opening_tags.get(offset)
            closing_tag = self.closing_tags.get(offset)
            if opening_tag:
                xml_string += "<%s>" % opening_tag[0]
            if closing_tag:
                xml_string += "</%s>" % closing_tag[0]
            xml_string += char
            offset += 1
        print xml_string
    

class XmlDocument:

    """An XmlDocument contains the parsed XML created by the XML parser. It contains a
    list of DocElements which at parse time is grown one element at a time, appending new
    elements at the end. This list of DocElements correclty reflects the XML document
    immediately after parsing, but note that the list is not updated when elements are
    later added or removed. Each DocElement links to the previous and next element. A tags
    dictionary is maintained to provide quick access to opening elements in the document.

    Instance variables
       elements - a list of XmlDocElements
       tags - a dictionary of tags, indexed on tag names, values are lists
       last_index - index of last element added """


    def __init__(self):

        """Set the elements and tags variables to an empty list and an empty
        dictionary and set last_index to -1, indicating that no
        elements have been added yet."""

        self.elements = []
        self.tags = {}
        self.last_index = -1

        
    def __getitem__(self,i):

        """Get item from the elements variable."""

        return self.elements[i]

    
    def __setitem__(self, i, val):

        """Set item in the elements variable."""

        self.elements[i] = val

        
    def get_tags(self, tagname):

        """Return the list of tags from the tag dictionary, takes a tag name
        as an argument."""

        return self.tags.get(tagname, [])

    
    def remove_tags(self, tagname):

        """Remove tags from the linked list, takes a tag name as an
        argument. This is a dangerous method because it relies on the
        tag dictionary being up-to-date."""

        tags = self.tags.get(tagname, [])
        for tag in tags:
            tag.remove()

            
    def insert_dct(self, dct, content_tag):

        """Insert the DCT as a TIMEX3 tag just before the first content
        tag. This is necessary because the DCT is usually not part of
        the main text. Need to figure out what to do if the DCT does
        happen to be in the main text."""

        tag = self.get_tags(content_tag)[0]
        t1 = XmlDocElement("\n")
        t2 = XmlDocElement('<s>', tag='s')
        t3 = create_dct_element(dct)
        t4 = XmlDocElement(dct)
        t5 = XmlDocElement('</TIMEX3>', tag='TIMEX3')
        t6 = XmlDocElement('</s>', tag='s')
        for t in (t6, t5, t4, t3, t2, t1):
            tag.insert_element_after(t)

            
    def set_element_list(self, xmlDocElements):

        """Set the contents of the XmlDocument, both self.elements and
        self.tags. This works if xmlDocElements is properly linked."""

        self.elements = xmlDocElements
        self.tags = {}
        for xmlDocElement in xmlDocElements:
            if xmlDocElement.is_opening_tag():
                self.add_to_tags_dictionary(xmlDocElement.tag, xmlDocElement)

                
    def add_to_tags_dictionary(self, tagname, tag):

        """Add a tag to the tag dictionary.
        Arguments
           tagname - a string
           tag - an XmlDocElement
        No return value."""

        if not self.tags.has_key(tagname):
            self.tags[tagname] = []
        self.tags[tagname].append(tag)

        
    def add_opening_tag_element(self, tagname, attrs, string):

        """Append a XmlDocElement to the elements list. 
        Arguments
           tagname - a string
           attrs - a dictionary
           string - a string that represents the entire tag"""

        element = XmlDocElement(string, tag=tagname, attrs=attrs)
        self.add_to_tags_dictionary(tagname, element)
        self._add_doc_element(element)

        
    def add_closing_tag_element(self, tagname, string):

        """Append an XmlDocElement to the elements list.

        Arguments
           tagname - a string
           string - a string that represents the closing tag """
        self._add_doc_element( XmlDocElement(string, tag=tagname) )

        
    def add_data_element(self, chardata):

        """Append an XmlDocElement to the elements list. If chardata
        is a string with non-whitespace characters, and if the
        previous element was also chardata dat included non-whitespace
        characters, then no new XmlDocElement will be added, but the
        current chrdata will be appended to the previous one.

        Arguments
           chardata - a string that represents the data element"""

        last_index = self._get_last_index()
        if last_index > -1:
            previous_element = self.elements[last_index]
            if not previous_element.is_tag():
                if previous_element.content.strip() and chardata.strip():
                    previous_element.content += chardata
                    # somehow, the method also worked fine without
                    # this return statement, but it should not have
                    return
        new_element = XmlDocElement(chardata)
        new_element.data = True
        self._add_doc_element(new_element)

        
    def add_default_element(self, string):

        """Append an XmlDocElement to the elements list.

        Arguments
           string - a string that represents the default element"""

        self._add_doc_element( XmlDocElement(string) )

        
    def _add_doc_element(self, current_element):

        """Append an XmlDocElement to the elements variable. Sets the previous
        field of the added element and the next field of the previous
        element is there was one. Also increments the last_index
        variable."""

        previous_element = None
        last_index = self._get_last_index()
        if last_index > -1:
            previous_element = self.elements[last_index]
            previous_element.set_next(current_element)
        current_element.set_previous(previous_element)
        self.elements.append(current_element)
        self._increment_last_index()

        
    def _get_last_index(self):

        return self.last_index

    
    def _increment_last_index(self):

        self.last_index = self.last_index + 1

        
    def get_tag_contents_as_xmldocs(self, tagname):

        """Return a list of new XmlDocument that consists of all
        XmlDocElements contained in all occurrences of the specified
        tagname. Includes the tagname as the root of each new
        XmlDocument.

        Note that the xmldocs returned are weird in one sense: the
        previous of the first element and the next of the last element
        are not set to None. We could set slice[0].previous and
        slice[-1].next to None, but then this new document would be
        cut off from its context in the XmlDocument of the entire
        input document."""

        xmldocs = []
        for tag in self.get_tags(tagname):
            slice = tag.get_slice()
            xmldoc = XmlDocument()
            xmldoc.set_element_list(slice)
            xmldocs.append(xmldoc)
        return xmldocs


    def populate_doc_from_list(self, docElements):

        """Populate a new XmlDoc from a list of XmlDocElements."""

        for docElement in docElements:
            el = docElement.copy()
            if self.elements:
                previous_element = self.elements[-1]
                previous_element.next = el
                el.previous = previous_element
            self.elements.append(el)
            if el.is_opening_tag():
                self.add_to_tags_dictionary(el.tag, el)    

                
    def get_closing_tag(self):

        """Return the closing tag, which is not necessarily the last element
        of the xml document. Returns None if no closing tag was found."""

        index = -1
        while True:
            try:
                element = self[index]
                if element.is_closing_tag():
                    return element
                index = index -1
            except IndexError:
                return None

            
    def add_tlink(self, reltype, id1, id2, origin):

        """Insert a tlink tag just before the closing tag of the document.

        Arguments
           reltype - a string
           id1 - an eiid or a tid
           id2 - an eiid or a tid
           origin - a string"""

        attrs = create_tlink_attributes(reltype, id1, id2, self.new_link_id(), origin)
        string = create_content_string('TLINK', attrs)
        new_opening_element = XmlDocElement(string, tag='TLINK', attrs=attrs)
        new_closing_element = XmlDocElement('</TLINK>', tag='TLINK')
        closing_tag = self.get_closing_tag()
        closing_tag.insert_element_before(new_opening_element)
        closing_tag.insert_element_before(new_closing_element)
        self.add_to_tags_dictionary('TLINK', new_opening_element)

        
    def add_arglink(self, eventID, argID, argTag='lex', role='UNKNOWN'):

        """Insert a arglink tag just before the closing tag of the document.
        Arguments
           eventID - an eid
           argID - an id, usually an lid from a lex tag
           argTag - a string, usually 'lex'
           role - a string"""

        attrs = {'eventID': eventID, 'argID': argID, 'argTag': argTag, 'role': role }
        string = create_content_string('ARGLINK', attrs)
        new_opening_element = XmlDocElement(string, tag='ARGLINK', attrs=attrs)
        new_closing_element = XmlDocElement('</ARGLINK>', tag='ARGLINK')
        closing_tag = self.get_closing_tag()
        closing_tag.insert_element_before(new_opening_element)
        closing_tag.insert_element_before(new_closing_element)
        self.add_to_tags_dictionary('ARGLINK', new_opening_element)

        
    def new_link_id(self):

        """Return a new unique linkid."""

        # NOTE: May want to spend some time doing it a tad more efficient
        link_ids = {}
        for link in self.get_tags('ALINK') + self.get_tags('SLINK') + self.get_tags('TLINK'): 
            link_id = link.attrs['lid']
            link_id = int(link_id[1:])
            link_ids[link_id] = True
        new_id = 1
        while True:
            if not link_ids.has_key(new_id):
                return "l%d" % new_id
            new_id = new_id + 1

            
    def save_to_file(self, filename):

        """ Print all document elements to a file with the given filename."""

        # NOTE: Cannot use a simple loop over the self.elements field
        # because it only has the original sequence of tags and
        # insertions and deletions are not maintained on it. Assumes
        # that the first element of self.elements is always the first
        # element of the XML file, even if the file has been changed.
        outfile = open(filename, "w")
        element = self.elements[0]
        while element:
            string = element.get_content()
            string = string.encode('ascii', 'replace')
            string = protectNode(string)
            outfile.write(string)
            element = element.get_next()


    def toString(self):

        """return a string representation of self as would be printed
        to a file"""

        element = self.elements[0]
        returnString = ""
        while element:
            nextString = element.get_content()
            nextString = nextString.encode('ascii', 'replace')
            nextString = protectNode(nextString)
            returnString += nextString
            element = element.get_next()
        return returnString

    
    def pretty_print(self):

        """Pretty printer for XmlDocuments. Pretty prints the list of elements
        and prints the tag dictionary to standard output."""

        print "\n%s\n\n<<XmlDocElements>>\n" % str(self)
        element = self.elements[0]
        while element:
            element.pretty_print(indent='   ')
            element = element.get_next()
        print "\n<<TagDictionary>>",
        for tag in self.tags.keys():
            print "\n\n[" + tag + '] ',
            for el in self.tags[tag]:
                print str(el.id),


class XmlDocElement:
    
    """ An XmlDocElement initially is an element derived from XML parsing using an
    instance of the Parser class. Its content field contains a tag or character data
    (which could be derived from a default handler, which deals with the xmldec as well as
    processing instructions etc). During further Tarsqi processing, 'pure' charData may be
    replaced with strings that contain tags. The previous and next fields contain another
    XmlDocElement or None for the first and last XmlDocElements of the document.

    Instance variables
       content - a string
       tag - None or a string
       data - boolean, depending on whether created from character data
       attrs - None or a dictionary
       previous - None or an XmlDocElement
       next - None or an XmlDocElement
       deleted - True|False
       id - unique element id"""

    
    def __init__(self, string, tag=None, attrs=None, data=False):

        """Initialization of an XmlDocElement using string representation, tag
        name (if any) and attribute dictionary (if any)."""

        global elementID
        elementID = elementID + 1
        self.content = string
        self.tag = tag
        self.data = data
        self.attrs = attrs
        self.previous = None
        self.next = None
        self.deleted = False
        self.id = elementID

        
    def __str__(self):

        """Print class plus the id and content values."""

        content_str = self.content.replace("\n", ' ')
        #return "XmlDocElement { id=%s , content=%s }" % (str(self.id), content_str)
        return "XmlDocElement(%s): %s" % (str(self.id), content_str)


    def copy(self):

        """Returns a copy of self. All instance variables are copied,
        except for previous and next, which are set to None."""

        newElement = XmlDocElement(self.content, self.tag)
        # must look into how this elementID works in non-standard
        # contexts
        if self.attrs:
            newElement.attrs = {}
            for (key, val) in self.attrs.items():
                newElement.attrs[key] = val
        newElement.id = self.id
        newElement.previous = None
        newElement.next = None
        newElement.deleted = False
        return newElement
    
    
    def get_previous(self):

        """Return the value of previous"""

        return self.previous

    
    def get_next(self):

        """Return the value of next"""

        return self.next

    
    def get_content(self):

        """Return the value of content"""

        return self.content

    
    def get_tag(self):

        """Return the value of tag"""

        return self.tag

    
    def is_tag(self):

        """Return None (False) or a non-empty string (True)."""

        return self.tag

    
    def is_opening_tag(self):

        """Return True if the XmlDocElement is an opening tag, return False
        otherwise."""

        return self.tag and self.content[1] != '/'

    
    def is_closing_tag(self):

        """Return True if the XmlDocElement is a closing tag, return False
        otherwise."""

        return self.tag and self.content[1] == '/'


    def is_text_element(self):

        """Return True if the element is a text element."""

        return self.data
    

    def set_next(self, doc_element):

        """Set the value of next to the given XmlDocElement."""

        self.next = doc_element

        
    def set_previous(self, doc_element):

        """Set the value of previous to the given XmlDocElement."""

        self.previous = doc_element

        
    def collect_content(self):

        """Return the content of a tag. Result is undefined if called on
        XmlDocElements that aren't tags. """

        list = self.collect_content_list()
        return ''.join(list)

        
    def collect_text_content(self):

        """Return the text content of a tag. Result is undefined if called
        on XmlDocElements that aren't tags. """

        list = self.collect_content_list()
        list = [item for item in list if item.is_text_node()]
        return ''.join(list)
        

    def collect_content_list(self):

        """ Get the content included in a tag, does not include the current
        opening and closing tags. """

        content = []
        tag = self.tag
        end_tag_found = False
        current_element = self
        while not end_tag_found:
            current_element = current_element.get_next()
            if tag == current_element.tag:
                return content
            content.append(current_element.content)

            
    def collect_text_content(self):

        """ Get the text content included in a tag."""

        content = ''
        tag = self.tag
        end_tag_found = False
        current_element = self
        while not end_tag_found:
            current_element = current_element.get_next()
            if tag == current_element.tag:
                return content
            if not current_element.tag:
                content += current_element.content

                
    def collect_contained_tags(self):

        """Return a list with all opening tags contained in the tag."""

        contained_tags = []
        tag = self.tag
        current_element = self
        while True:
            current_element = current_element.get_next()
            if tag == current_element.tag:
                return contained_tags
            if current_element.is_opening_tag():
                contained_tags.append(current_element)

                
    def get_slice(self):

        """ Get a slice of the document, starting at self and ending at the
        closing tag. Note that the first element will have a previous
        and the last element will have a next (unless the tag is the
        root of the xml document)."""

        slice = [self]
        tag = self.tag
        current_element = self
        while True:
            current_element = current_element.get_next()
            if current_element is None:
                logger.error('Reached end of document before closing tag was found')
            slice.append(current_element)
            if tag == current_element.tag:
                return slice

            
    def get_slice_till(self, id):

        """Get the document slice starting with self and ending with the
        element with the given id."""

        contained_tags = [self]
        current_element = self
        while True:
            current_element = current_element.get_next()
            contained_tags.append(current_element)
            if id == current_element.id:
                return contained_tags

            
    def replace_content(self, text):

        """Replaces the list of document elements from itself till the closing
        element with one document element containing the text string."""

        closing_tag = self.get_closing_tag()
        element = XmlDocElement(text)
        element.set_previous(self)
        element.set_next(closing_tag)
        self.set_next(element)
        closing_tag.set_previous(element)

        
    def replace_content_with_list(self, element_list):

        """Replaces the list of document elements from itself till the closing
        element with a new list of document elements.
        Arguments:
           element_list - a list of XmlDocElements."""

        closing_tag = self.get_closing_tag()
        current_tag = self
        for element in element_list:
            # this is a hack intended to skip this tag, needs to be
            # solved at the link insertion level of slinket et al
            if element.tag == 'fragment':
                continue
            element.set_previous(current_tag)
            current_tag.set_next(element)
            current_tag = element
        current_tag.set_next(closing_tag)
        closing_tag.set_previous(current_tag)

        
    def get_closing_tag(self):

        """Return the closing tag for the XmlDocElement. The return value is
        not defined when this is called on a non opening tag."""

        # TODO: needs to be made more general, now it gives the wrong
        # result if you have embedded tags with the same name (with
        # "<np><np>door</np></np>" the first </np> will be returned).
        next_element = self.get_next()
        while next_element:
            if next_element.get_tag() == self.tag:
                return next_element
            next_element = next_element.get_next()
        return None

    
    def insert_string_after(self, string):

        """Take a string and insert it as an XmlDocElement right after the
        current element."""

        element = XmlDocElement(string)
        self.insert_element_after(element)

        
    def insert_element_after(self, doc_element):

        """Insert a document element right after the current one."""

        old_next_element = self.get_next()
        self.set_next(doc_element)
        doc_element.set_previous(self)
        doc_element.set_next(old_next_element)
        old_next_element.set_previous(doc_element)

        
    def insert_tag_before(self, tagname, string):

        """Insert a tag right before the current element.
        Arguments
           tagname - a string
           string - string representation of the entire tag"""

        element = XmlDocElement(string,tag=tagname)
        self.insert_element_before(element)

        
    def insert_element_before(self, doc_element):

        """Insert a document element right before the current one."""

        old_previous_element = self.get_previous()
        self.set_previous(doc_element)
        doc_element.set_next(self)
        doc_element.set_previous(old_previous_element)
        old_previous_element.set_next(doc_element)

        
    def remove(self):

        """Remove the XmlDocElement. This will not destroy the element but
        remove it from the linked list. If the element is an opening
        tag, then the closing tag will be removed as well. The
        behaviour of this method is undefined for closing tags and for
        the first and last elements of the linked list. """

        previous = self.get_previous()
        next = self.get_next()
        previous.set_next(next)
        next.set_previous(previous)
        if self.is_opening_tag():
            closing_tag = self.get_closing_tag()
            closing_tag.remove()

            
    def pretty_print(self, indent=''):

        """Pretty printer for XmlDocElements, prints the content of the element."""

        print indent + 'ELEMENT(' + str(self.id) + '): ' + self.content




def create_tlink_attributes(reltype, id1, id2, link_id, origin):

    """Create a dictionary with tlink attibutes.
    Arguments:
       reltype  - string
       id1 - string
       id2 - string
       link_id - string of the form l\d+
       origin - string
    Returns a dictionary."""

    # NOTE: this method should perhaps be moved elsewhere, possibly to
    # a Tlink class
    attrs = {}
    if id1.startswith('e'):
        attrs['eventInstanceID'] = id1
    else:
        attrs['timeID'] = id1
    if id2.startswith('e'):
        attrs['relatedToEventInstance'] = id2
    else:
        attrs['relatedToTime'] = id2
    attrs['relType'] = reltype
    attrs['lid'] = link_id
    attrs['origin'] = origin
    return attrs


def create_dct_element(dct):

    """Returns an XmlDocElement that represents the Document Creation Time
    as an opening tag. The argument is a string of the format YYYYMMDD."""

    string = \
        '<TIMEX3 tid="t0" TYPE="DATE" VAL="'+ \
        dct + \
        '" functionInDocument="DOCUMENT_CREATION_TIME">'
    attributes = {
        'tid': 't0',
        'TYPE': 'DATE',
        'VAL': dct,
        'functionInDocument': 'DOCUMENT_CREATION_TIME' }
    return XmlDocElement(string, tag='TIMEX3', attrs=attributes)


def create_content_string(name, attrs):

    """Utility method to take a tag name and a dictionary of attributes
    and create a tag from it."""

    string = '<'+name
    for att in attrs.items():
        nameAtt = att[0]
        value = att[1]
        if not (name is None or value is None):
            string =string+' '+nameAtt+'="'+value+'"'
    string = string+'>' 
    return string


            

        
if __name__ == '__main__':
    
    IN = sys.argv[1]
    OUT = sys.argv[2]
    
    xmlfile = open(IN,"r")
    p = Parser()
    DOC = p.parse(xmlfile)
    DOC.save_to_file(OUT)

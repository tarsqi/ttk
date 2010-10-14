import re
from xml.parsers.expat import ExpatError
from xml.sax.saxutils import escape

from utilities import logger
import docmodel.xml_parser

# the weird thing here is that the following was all of a sudden impossible after I added
# "from utilities.xml_utils import emptyContentString" to common_modules/document
#from docmodel.xml_parser import Parser
#from docmodel.xml_parser import XmlDocElement


re_protect1 = re.compile('&(?!amp;)')


def endElementString(tagname):
    """Return the string representation of a closing tag given the tagname."""
    return '</'+tagname+'>'

def startElementString(tagname, attrs):
    """Return the string representation of an opening tag given the tagname and a dictionary
    of attributes."""
    string = '<'+tagname
    for att in attrs.items():
        name = att[0]
        value = att[1]
        if not (name is None or value is None):
            string = string+' '+name+'="'+value+'"'
    string = string+'>'
    return string

def emptyContentString(tagname, attrs):
    """Return the string representation of a non-consuming tag given the tagname and a
    dictionary of attributes."""
    string_as_opening_string = startElementString(tagname, attrs)
    return string_as_opening_string[:-1] + '/>'

def protect_text(text):
    """Take a text string and protect XML special characters. Should also do something
    with non-ascii characters as well as with things like &#2435; and &quote;. Should use
    xml.sax.saxutils methods."""
    text = re_protect1.sub('&amp;', text)
    text = text.replace('<', '&lt')
    text = text.replace('>', '&gt')
    return text.encode('ascii', 'xmlcharrefreplace')


def merge_tags_from_files(infile1, infile2, merged_file):
    """Merge the tags from infile1, which has all tags from the input, with tags from
    infile2, which has only s, lex and TIMEX3 tags. The lex tags are used as the pivots
    and it is assumed that both files contain the same amount of lex tags."""
    doc1 = docmodel.xml_parser.Parser().parse_file(open(infile1,"r"))
    doc2 = docmodel.xml_parser.Parser().parse_file(open(infile2,"r"))
    merge_tags_from_xmldocs(doc1, doc2)
    # save the Document object of infile1 as the resulting merged file
    doc1.save_to_file(merged_file)
        

def merge_tags_from_xmldocs(doc1, doc2):

    """Merge the tags from doc1, which has all tags from the input, with tags from doc2,
    which has only s, lex and TIMEX3 tags. The lex tags are used as the pivots and it is
    assumed that both files contain the same amount of lex tags. The TIMEX3 tags from doc2
    are merged into doc1."""

    # add lex_id values to the lex tags
    _mark_lex_tags(doc1)
    _mark_lex_tags(doc2)

    # get the timexes and embedded lex tags from infile2, and create
    # index of the lex tags of infile1 using lex_id
    extended_timexes = _get_timextags_with_contained_lextags(doc2)
    lexid_to_lextag = _create_lexid_index(doc1)

    for extended_timex in extended_timexes:

        # get first and last document element of infile1
        (timex_tag, lex_ids) = extended_timex
        first_element = lexid_to_lextag[lex_ids[0]]
        last_element = lexid_to_lextag[lex_ids[-1]].get_closing_tag()

        # get the entire sequence that is to be embedded in the timex tag
        sequence = first_element.get_slice_till(last_element.id)
        (first_element, last_element) = _extent_sequence(first_element, last_element, sequence)
        sequence_string = ''.join([el.content for el in sequence])
        
        # check whether this sequence, when embedded in a tag, results
        # in well-formed XML, if so, add the new timex tag to infile1,
        try:
            docmodel.xml_parser.Parser().parse_string("<TAG>%s</TAG>" % sequence_string)
            # insert opening and closing timex tags
            first_element.insert_element_before(timex_tag)
            last_element.insert_element_after(
                docmodel.xml_parser.XmlDocElement('</TIMEX3>', 'TIMEX3'))
        except ExpatError:
            # if result was not well-formed, try adding element on both sides
            first_element = _extent_sequence_left(sequence)
            last_element = _extent_sequence_right(sequence)
            sequence_string = ''.join([el.content for el in sequence])
            try:
                docmodel.xml_parser.Parser().parse_string("<TAG>%s</TAG>" % sequence_string)
                first_element.insert_element_before(timex_tag)
                last_element.insert_element_after(
                    docmodel.xml_parser.XmlDocElement('</TIMEX3>', 'TIMEX3'))
            except ExpatError:
                logger.warn("Could not wrap TIMEX3 tag around\n\t %s" % sequence_string)

        
def _mark_lex_tags(doc):
    """Add a unique id to each lex tag. """
    lex_id = 0
    # This used to loop over doc.elements, but it is more robust to use get_next() for
    # those case where the xmldoc has been updated.
    element = doc.elements[0]
    while element:
        if element.is_opening_tag() and element.tag == 'lex':
            lex_id = lex_id + 1
            element.lex_id = lex_id
        element = element.get_next()

def _get_timextags_with_contained_lextags(doc):
    """Get all TIMEX3 tags, and associated them with the lex tags that are included in
    them."""
    timextags_with_lextags = []
    for timextag in doc.tags.get('TIMEX3',[]):
        lex_elements = []
        timex_elements = timextag.collect_contained_tags()
        for timex_element in timex_elements:
            if timex_element.tag == 'lex':
                lex_elements.append(timex_element.lex_id)
        timextags_with_lextags.append([timextag, lex_elements])
    return timextags_with_lextags

def _create_lexid_index(doc):
    """Index all opening lex tags."""
    index = {}
    # This used to loop over doc.elements, but it is more robust to use get_next() for
    # those case where the xmldoc has been updated.
    element = doc.elements[0]
    while element:
        if element.is_opening_tag() and element.tag == 'lex':
            index[element.lex_id] = element
        element = element.get_next()
    return index

def _extent_sequence(first_element, last_element, sequence):
    """Extent the sequence with one to the leftor right if the number of opening and
    closing tags in the sequence are not equal. Returns the first and last element of the
    new sequence and changes the sequence as side effect."""
    opening_tags = [el for el in sequence if el.is_opening_tag()]
    closing_tags = [el for el in sequence if el.is_closing_tag()]
    if len(opening_tags) < len(closing_tags):
        first_element = _extent_sequence_left(sequence)
    elif len(opening_tags) > len(closing_tags):
        last_element = _extent_sequence_right(sequence)
    return(first_element, last_element)

def _extent_sequence_left(sequence):
    """Extent the sequence with one element to the left, but only if that element is an
    opening tag. Takes a sequence of XmlDocElements, potentially adding an element at the
    front. Returns the element added."""
    first = sequence[0]
    previous = first.get_previous()
    if previous.is_opening_tag():
        sequence.insert(0, previous)
        return previous
    else:
        return first
    
def _extent_sequence_right(sequence):
    """Extent the sequence with one element to the right, but only if that element is an
    closing tag. Takes a sequence of XmlDocElements, potentially adding an element at the
    end. Returns the element added."""
    last = sequence[-1]
    next = last.get_next()
    if next.is_closing_tag():
        sequence.append(next)
        return next
    else:
        return last





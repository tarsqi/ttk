
import time
from xml.sax.saxutils import escape

from docmodel.xml_parser import Parser
from docmodel.document import TarsqiDocument
from docmodel.document import TarsqiDocParagraph

    
class DefaultParser:

    """The simplest parser, much like the SimpleXml parser for the old simple-xml
    doctype. It creates a TarsqiDocument instance with a single TarsqiDocParagraph in
    it. It finds the target tag, which is assumed to be TEXT, and considers all text
    inside as the content of the single TarsqiDocParagraph.

    TODO: make this more general in that it should be able to deal with more than one tag,
    perhaps defined in the processing parameters.

    TODO: make this work with pure text input, taking all content, perhaps a default
    should be to take all text if no target tag could be found.
    
    Instance variables:
       docsource - a SourceDoc instance
       elements - a list with one TarsqiDocParagraph element
       xmldoc - an XmlDocument instance
       metadata - a dictionary"""

    
    def __init__(self):
        """Not used now but could be used to hand in specific metadata parsers or other
        functionality that cuts through genres."""
        pass

    def parse(self, docsource):
        """Return an instance of TarsqiDocument. Get the TEXT tag and the associated
        source string and populate the TarsqiDocument with the following content: (i)
        docsource embeds the SourceDoc instance that was created by the SourceParser, (ii)
        elements contains one element, a TarsqiDocParagraph for the TEXT, (iii) xmldoc
        contains an XmlDocument created from the TEXT, (iv) metadata simply contains a DCT
        set to today."""
        target_tag = self._find_target_tag(docsource)
        text = docsource.text[target_tag.begin:target_tag.end]
        #xmldoc = Parser().parse_string("<TEXT>%s</TEXT>" % escape(text))
        #elements = [TarsqiDocParagraph(target_tag.begin, target_tag.end, text, xmldoc)]
        element_offsets = split_paragraph(text)
        elements = []
        for (p1, p2) in element_offsets:
            xmldoc = Parser().parse_string("<TEXT>%s</TEXT>" % escape(text[p1:p2]))
            elements.append(TarsqiDocParagraph(p1, p2, text[p1:p2], xmldoc))
        for e in elements:
            e.add_source_tags(docsource.tags.all_tags())
            e.source_tags.index()
        metadata = { 'dct': get_today() }
        return TarsqiDocument(docsource, elements, metadata, xmldoc)
    
    def _find_target_tag(self, docsource):
        """Return the content of the TEXT tag, raise an error if not succesful."""
        tag = docsource.tags.find_tag('TEXT')
        if tag is None:
            raise DocParserError('Cannot parse docsource, no target_tag')
        else:
            return tag



def split_paragraph(text):

    """Very simplistic way to split a paragraph into more than one paragraph, simply by
    looking for an empty line."""

    text_end = len(text)
    (par_begin, par_end) = (None, None)
    (p1, p2, space) = slurp_space(text, 0)
    par_begin = p2
    seeking_space = False
    paragraphs = []
    
    while (p2 < text_end):
        if not seeking_space:
            (p1, p2, token) = slurp_token(text, p2)
            par_end = p2
            seeking_space = True
        else:
            (p1, p2, space) = slurp_space(text, p2)
            seeking_space = False
            if space.count("\n") > 1:
                par_end = p1
                paragraphs.append((par_begin, par_end))
                par_begin = p2
                par_end = None

    if seeking_space and p2 > par_begin:
        paragraphs.append((par_begin, par_end))

    return paragraphs



def slurp(text, offset, test):
    """Starting at offset in text, find a substring where all characters pass test. Return
    the begin and end position and the substring."""
    begin = offset
    end = offset
    length = len(text)
    while offset < length:
        char = text[offset]
        if test(char):
            offset += 1
            end = offset
        else:
            return (begin, end, text[begin:end])
    return (begin, end, text[begin:end])
    
def slurp_space(text, offset):
    def test_space(char): return char.isspace()
    return slurp(text, offset, test_space)

def slurp_token(text, offset):
    def test_nonspace(char): return not char.isspace()
    return slurp(text, offset, test_nonspace)




class TimebankParser:

    """Preliminary class for Timebank parsing. Will likely not work, but is storing some DCT
    processing functionality (which probably needs to be moved out of the class). """
    

    def __init__(self):
        
        """This could be used to hand in specific metadata parsers or other functionality that
        cuts through genres."""

        pass


    def parse(self, docsource):

        """Get the TEXT tag and the associated source string. Then create an XmlDocument
        for that string and simple metadata for the document by setting the DCT to
        today. Return an instance of TarsqiDocument."""

        target_tag = self._find_target_tag(docsource)
        text = docsource.text[target_tag.begin:target_tag.end]
        xmldoc = Parser().parse_string("<TEXT>%s</TEXT>" % text)
        dct = self.parse_dct()
        metadata = { 'dct': dct }
        return TarsqiDocument(docsource, xmldoc, metadata)


    def _find_target_tag(self, docsource):
        
        for t in docsource.tags:
            if t.name == 'TEXT':
                return t
        raise DocParserError('Cannot parse docsource, no target_tag')


    def parse_dct(self, xmldoc):

        """Takes an XmlDocument, extracts the document creation time, and returns it as a
        string of the form YYYYMMDD.

        TODO: update for use with DocSource class."""

        # set DCT default
        dct = get_today()

        docsource = self._get_doc_source(xmldoc)

        if docsource == 'ABC':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = docno[3:11]
            
        elif docsource == 'AP':
            fileid = xmldoc.tags['FILEID'][0].collect_content().strip()
            result = re.compile("(AP-NR-)?(\d+)-(\d+)-(\d+)").match(fileid)
            if result:
                (crap, month, day, year) = result.groups()
                dct = "19%s%s%s" % (year, month, day)
            else:
                logger.warn("Could not get date from %s" % fileid)
                
        elif docsource == 'APW':
            date_time = xmldoc.tags['DATE_TIME'][0].collect_content().strip()
            result = re.compile("(\d+)/(\d+)/(\d+)").match(date_time)
            if result:
                (month, day, year) = result.groups()
                dct = "%s%s%s" % (year, month, day)
            else:
                logger.warn("Could not get date from %s" % fileid)
            
        elif docsource == 'CNN':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = docno[3:11]

        elif docsource == 'NYT':
            date_time = xmldoc.tags['DATE_TIME'][0].collect_content().strip()
            result = re.compile("(\d+)/(\d+)/(\d+)").match(date_time)
            if result:
                (month, day, year) = result.groups()
                dct = "%s%s%s" % (year, month, day)
            else:
                logger.warn("Could not get date from %s" % fileid)

        elif docsource == 'PRI':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = docno[3:11]

        elif docsource == 'SJMN':
            pubdate = xmldoc.tags['PUBDATE'][0].collect_content().strip()
            dct = '19' + pubdate

        elif docsource == 'VOA':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = docno[3:11]

        elif docsource == 'WSJ':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = '19' + docno[3:9]

        elif docsource == 'eaX':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = '19' + docno[2:8]

        elif docsource == 'ea':
            docno = xmldoc.tags['DOCNO'][0].collect_content().strip()
            dct = '19' + docno[2:8]

        return dct

    
    def _get_doc_source(self, xmldoc):
        
        """Returns the name of the content provider."""

        tag_DOCNO = xmldoc.tags['DOCNO'][0]
        content = tag_DOCNO.collect_content().strip()
        # TimeBank has only these providers
        for str in ('ABC', 'APW', 'AP', 'CNN', 'NYT', 'PRI', 'SJMN', 'VOA', 'WSJ', 'ea', 'ed'):
            if content.startswith(str):
                return str
        logger.warn("Could not determine document source from DOCNO tag")
        return 'GENERIC'



class MetaDataParser_ATEE:

    """This is how DCT parsing was done for ATEE document. Must decide whether neta data
    parsers are separate classes (like here) or are part of the Parser (see
    TimebankParser)."""
    
    def parse_dct(self, xmldoc):
        """All ATEE documents have a DATE tag with a value attribute, the value of that attribute
        is returned."""
        date_tag = xmldoc.tags['DATE'][0]
        return date_tag.attrs['value']

    
def get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime());


class DocParserError(Exception): pass

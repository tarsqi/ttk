
import time

from docmodel.xml_parser import Parser


    
class DefaultParser:

    """The simplest parser, much like the SimpleXml parser for the old simple-xml
    doctype. Gets the TEXT tag and the associated source string. Then creates an
    XmlDocument for that string and simple metadata for the document by setting the DCT to
    today. """
    
    def __init__(self):

        pass


    def parse(self, docsource):

        """Get the TEXT tag and the associated source string. Then create an XmlDocument
        for that string and simple metadata for the document by setting the DCT to
        today. Return an instance of SuperDoc."""
            
        target_tag = self._find_target_tag(docsource)
        text = docsource.source[target_tag.begin:target_tag.end]
        xmldoc = Parser().parse_string("<TEXT>%s</TEXT>" % text)
        dct = get_today()
        metadata = { 'dct': dct }
        return SuperDoc(docsource, xmldoc, metadata)


    def _find_target_tag(self, docsource):
        
        for t in docsource.tags:
            if t.name == 'TEXT':
                return t
        raise DocParserError('Cannot parse docsource, no target_tag')


    
class SuperDoc:

    """Placeholder for what will be the new Document class, which contains minimal
    document structure in its elements variable. Elements are typed and include the source
    string and a dictionary of tags. For now simply use an XmlDocument so we interface
    easier with the old approach. Should live in its own module. """
    
    def __init__(self, docsource, xmldoc, metadata):

        self.docsource = docsource
        self.xmldoc = xmldoc
        self.elements = []
        self.metadata = metadata
        

def get_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime());


class DocParserError(Exception): pass


import time

from docmodel.xml_parser import Parser

    
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

    def get_dct(self):
        return self.metadata.get('dct')
    

def XXget_today():
    """Return today's date in YYYYMMDD format."""
    return time.strftime("%Y%m%d", time.localtime());


class DocParserError(Exception): pass

from mixins.parameters import ParameterMixin
from source_parser import TagRepository


class TarsqiDocument(ParameterMixin):

    """An instance of TarsqiDocument should contain all information that may be needed by
    the wrappers to do their work. It will contain minimal document structure in its
    elements variable. Elements will be typed and include the source string and a
    dictionary of tags. For now we simply use an XmlDocument so we interface easier with
    the old approach.

    Instance Variables:
       docsource - instance of DocSource
       xmldoc - instance of XmlDocument (used for now for heritage code)
       elements - list, not yet used
       metadata - a dictionary
       parameters - parameter dcitionary from the Tasqi instance
       
    Note that more variables will be needed. Currently, sseveral wrappers use data from
    the Tarsqi instance, should check what these data are and get them elsewhere,
    potentially by adding them here.

    Also note that now that parameters are available to the wrappers only through this
    class. Use the methods in the mixin class to access the parameters, these methods all
    start with 'getopt' and all they do is to access parameters."""
    
    def __init__(self, docsource, elements, metadata, xmldoc=None):
        self.docsource = docsource
        self.xmldoc = xmldoc
        self.elements = elements
        self.metadata = metadata
        self.parameters = {}
        
    def add_parameters(self, parameter_dictionary):
        self.parameters = parameter_dictionary
        
    def get_dct(self):
        return self.metadata.get('dct')
    


class TarsqiDocElement:

    def __init__(self, begin, end, text, xmldoc=None):
        self.begin = begin
        self.end = end
        self.text = text
        self.xmldoc = xmldoc
        self.tags = TagRepository()

    def __str__(self):
        return "\n<%s %d:%d>\n\n%s\n\n" % \
               (self.__class__, self.begin, self.end, self.text.encode('utf-8').strip())

    def is_paragraph(): return False

    
class TarsqiDocParagraph(TarsqiDocElement):

    def __init__(self, begin, end, text, xmldoc=None):
        TarsqiDocElement.__init__(self, begin, end, text, xmldoc)

    def is_paragraph(): return True


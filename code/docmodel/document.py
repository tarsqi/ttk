from copy import copy
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
       parameters - parameter dictionary from the Tasqi instance
       
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
    
    def pp(self, source=True, xmldoc=True, metadata=True, parameters=True, elements=True):
        if source: self.docsource.pp()
        if xmldoc: self.xmldoc.pp()
        if metadata:
            print "\nMETADATA DICTIONARY:", self.metadata, "\n"
        if parameters:
            print "\nPARAMETERS DICTIONARY:", self.parameters, "\n"
        if elements:
            for e in self.elements: e.pp()
        

class TarsqiDocElement:

    """Contains a slice from a TarsqiDocument. The slice is determined by the begin and
    end instance variables and the content of text is the slice from the source document.
    """
    
    def __init__(self, begin, end, text, xmldoc=None):
        self.begin = begin
        self.end = end
        self.text = text
        self.xmldoc = xmldoc
        self.source_tags = TagRepository()
        self.tarsqi_tags = TagRepository()

    def __str__(self):
        return "<%s %d:%d>\n\n%s" % \
               (self.__class__, self.begin, self.end, self.text.encode('utf-8').strip())

    def is_paragraph(): return False

    def get_text(self, p1, p2):
        return self.text[p1:p2]
    
    def add_source_tags(self, tag_repository):
        """Add all tags from a TagRepostitory (handed in from the SourceDoc) that fall
        within the scope of this element. Makes a shallow copy of the Tag from the
        SourceDoc TagRepository and updates the begin and end variables according to the
        begin position of the element."""
        for t in tag_repository:
            if t.begin >= self.begin and t.end <= self.end:
                t2 = copy(t)
                t2.begin -= self.begin
                t2.end -= self.begin
                self.source_tags.append(t2)
    
    def pp(self):
        print self
        self.source_tags.pp()
        self.tarsqi_tags.pp()
        
    
class TarsqiDocParagraph(TarsqiDocElement):

    def __init__(self, begin, end, text, xmldoc=None):
        TarsqiDocElement.__init__(self, begin, end, text, xmldoc)

    def is_paragraph(): return True

    

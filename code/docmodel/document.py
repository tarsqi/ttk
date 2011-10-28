import sys
from copy import copy
from mixins.parameters import ParameterMixin
from source_parser import TagRepository


class TarsqiDocument(ParameterMixin):

    """An instance of TarsqiDocument should contain all information that may be needed by
    the wrappers to do their work. It will contain minimal document structure in its
    elements variable, at this point just a list of TarsqiDocElements. Elements will be
    typed and include the source string and a dictionary of tags. 

    For now we also use an XmlDocument so we interface easier with the old approach, but
    the idea is that the xmldoc variable is going ot be phased out.

    Instance Variables:
       source - instance of DocSource
       xmldoc - instance of XmlDocument (used for now for heritage code)
       elements - list of TarsqiDocElements
       metadata - a dictionary
       parameters - parameter dictionary from the Tasqi instance
       
    Note that more variables will be needed. Currently, sseveral wrappers use data from
    the Tarsqi instance, should check what these data are and get them elsewhere,
    potentially by adding them here.

    Also note that parameters are available to the wrappers only through this class. Use
    the methods in the mixin class to access the parameters, these methods all start with
    'getopt' and all they do is access parameters."""
    
    #def __init__(self, docsource, elements, metadata, xmldoc=None):
    def __init__(self, docsource, metadata, xmldoc=None):
        self.source = docsource
        self.xmldoc = xmldoc
        self.elements = []
        self.metadata = metadata
        self.parameters = {}
        
    def add_parameters(self, parameter_dictionary):
        self.parameters = parameter_dictionary
        
    def get_dct(self):
        return self.metadata.get('dct')
    
    def pp(self, source=True, xmldoc=True, metadata=True, parameters=True, elements=True):
        if source: self.source.pp()
        if xmldoc: self.xmldoc.pp()
        if metadata: print "\nMETADATA DICTIONARY:", self.metadata, "\n"
        if parameters: print "\nPARAMETERS DICTIONARY:", self.parameters, "\n"
        if elements: 
            for e in self.elements: e.pp()

    def print_source(self, filename):
        self.source.print_source(filename)

    

class TarsqiDocElement:

    """Contains a slice from a TarsqiDocument. The slice is determined by the begin and
    end instance variables and the content of text is the slice from the source document.
    """

    ELEMENT_ID = 0
    
    def __init__(self, tarsqidoc, begin, end, xmldoc=None):
        self._assign_identifier()
        self.doc = tarsqidoc
        self.begin = begin
        self.end = end
        self.xmldoc = xmldoc
        self.source_tags = TagRepository()
        self.tarsqi_tags = TagRepository()

    def __str__(self):
        return "<%s #%d %d:%d>\n\n%s" % (self.__class__, self.id, self.begin, self.end, 
                                         self.get_text().encode('utf-8').strip())
            
    def _assign_identifier(self):
        self.__class__.ELEMENT_ID += 1
        self.id = self.__class__.ELEMENT_ID

    def is_paragraph(): return False

    def get_text(self, p1=None, p2=None):
        if p1 is None: p1 = self.begin
        if p2 is None: p2 = self.end
        return self.doc.source.text[p1:p2]
    
    def add_source_tags(self, tag_repository):
        """Add all tags from a TagRepostitory (handed in from the SourceDoc) that fall
        within the scope of this element. Makes a shallow copy of the Tag from the
        SourceDoc TagRepository and updates the begin and end variables according to the
        begin position of the element. Also incldue those tags where the start is before
        and the end is after the document."""
        for t in tag_repository:
            if (t.begin >= self.begin and t.end <= self.end) \
                    or (t.begin <= self.begin and t.end >= self.end):
                self.source_tags.append(copy(t))
    
    def pp(self):
        print "\n", self
        print "\n  <%s.source_tags>" % self.__class__
        self.source_tags.pp()
        print "\n  <%s.tarsqi_tags>" % self.__class__
        self.tarsqi_tags.pp()
        print
        
    
class TarsqiDocParagraph(TarsqiDocElement):

    def __init__(self, begin, end, text, xmldoc=None):
        TarsqiDocElement.__init__(self, begin, end, text, xmldoc)

    def is_paragraph(): return True

    

import sys, codecs
from copy import copy
from mixins.parameters import ParameterMixin
from source_parser import TagRepository


class TarsqiDocument(ParameterMixin):

    """An instance of TarsqiDocument should contain all information that may be needed by
    the wrappers to do their work. It will contain minimal document structure in its
    elements variable, at this point just a list of TarsqiDocElements. Elements will be
    typed and include the source string and a dictionary of tags. 

    Instance Variables:
       source - instance of DocSource
       doctree - instance of Document
       elements - list of TarsqiDocElements
       metadata - a dictionary
       parameters - parameter dictionary from the Tasqi instance
       counters - a set of counters used to create unique identifiers

    Note that more variables will be needed. Currently, several wrappers use data from
    the Tarsqi instance, should check what these data are and get them elsewhere,
    potentially by adding them here.

    Also note that parameters are available to the wrappers only through this class. Use
    the methods in the mixin class to access the parameters, these methods all start with
    'getopt' and all they do is access parameters.

    Also note that we may need a tarsqi_tags variable, to store those tags that are not
    internal to any of the elements. """
    
    def __init__(self, docsource, metadata):
        self.source = docsource
        self.elements = []
        self.metadata = metadata
        self.parameters = {}
        self.counters = { 'TIMEX3': 0, 'EVENT': 0 }

    def __str__(self):
        return "<%s on '%s'>" % (self.__class__, self.source.filename)
        
    def add_parameters(self, parameter_dictionary):
        self.parameters = parameter_dictionary
        
    def get_dct(self):
        return self.metadata.get('dct')
    
    def text(self, p1, p2):
        return self.source.text[p1:p2]

    def pp(self, source=True, elements=True):
        print "\n", self, "\n"
        for key, value in self.metadata.items():
            print "   metadata.%-17s  -->  %s" % (key, value)
        for key, value in self.parameters.items():
            print "   parameters.%-15s  -->  %s" % (key, value)
        if source:
            self.source.pp()
        if elements:
            for e in self.elements: e.pp()

    def next_event_id(self):
        self.counters['EVENT'] += 1
        return "e%d" % self.counters['EVENT']

    def print_source(self, fname):
        """Print the original source of the document, without the tags to file fname."""
        self.source.print_source(fname)

    def print_sentences(self, fname=None):
        """Write to file (or stadard output if no filename was given) a Python variable
        assignment where the content of the variable the list of sentences as a list of
        lists of token strings."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("sentences = ")
        fh.write(str(self.list_of_sentences()))
        fh.write("\n")

    def print_all(self, fname):
        """Write source string, source tags and ttk tags all to one file."""
        fh = codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("<ttk>\n")
        fh.write("<text>%s</text>\n" % self.source.text)
        fh.write("<source_tags>\n")
        for tag in self.source.tags.tags:
            fh.write("  %s\n" % tag.in_layer_format())
        fh.write("</source_tags>\n")
        fh.write("<ttk_tags>\n")
        for e in self.elements:
            for tag in e.tarsqi_tags.tags:
                fh.write("  %s\n" % tag.in_layer_format())
        fh.write("</ttk_tags>\n")
        fh.write("</ttk>\n")

    def print_source_tags(self, fname=None):
        """Prints all the tags from the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        for tag in self.source.tags.tags:
            fh.write(tag.in_layer_format()+"\n")

    def print_tarsqi_tags(self, fname=None):
        """Prints all the tarsqi tags added to the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        fh.write("<ttk>\n")
        for e in self.elements:
            for tag in e.tarsqi_tags.tags:
                fh.write('  ' + tag.in_layer_format() + "\n")
        fh.write("</ttk>\n")

    def _print_tags(self, tag_repository, fname=None):
        """Prints all the tarsqi tags added to the source documents to a layer file."""
        fh = sys.stdout if fname == None else codecs.open(fname, mode='w', encoding='UTF-8')
        for e in self.elements:
            for tag in tag_repository.tags:
                fh.write(tag.in_layer_format()+"\n")

    def list_of_sentences(self):
        sentences = []
        sentence = []
        for element in self.elements:
            # TODO: delegate to TarsqiDocParagraph?
            for t in element.tarsqi_tags.tags:
                if t.name == 's':
                    if sentence:
                        sentences.append(sentence)
                        sentence = []
                elif t.name == 'lex':
                    sentence.append(self.text(t.begin, t.end))
            if sentence:
                sentences.append(sentence)
            sentence = []
        return sentences
        

            
class TarsqiDocElement:
    """Contains a slice from a TarsqiDocument. The slice is determined by the begin
    and end instance variables and the content of text is the slice from the
    source document. The slice includes the tags that are relevant to this
    element. These tags have offsets that are relative to the entire document,
    these can be translated into local offsets using self.begin."""

    ELEMENT_ID = 0
    
    def __init__(self, tarsqidoc, begin, end):
        self._assign_identifier()
        self.doc = tarsqidoc
        self.begin = begin
        self.end = end
        self.source_tags = TagRepository()
        self.tarsqi_tags = TagRepository()

    def __str__(self):
        return "<%s #%d %d:%d>\n\n%s\n" % \
               (self.__class__, self.id, self.begin, self.end, 
                self.get_text().encode('utf-8').strip())
            
    def _assign_identifier(self):
        self.__class__.ELEMENT_ID += 1
        self.id = self.__class__.ELEMENT_ID

    def is_paragraph(): return False

    def get_text(self):
        """Return the text slice in this element."""
        return self.doc.text(self.begin, self.end)
    
    def add_source_tags(self, tag_repository):
        """Add all tags from a TagRepostitory (handed in from the SourceDoc) that fall
        within the scope of this element. Also includes tags whose begin is
        before and whose end is after the element. Makes a shallow copy of the
        Tag from the SourceDoc TagRepository."""
        # note that tag_repository is also available in self.doc.source.tags
        for t in tag_repository.tags:
            if (t.begin >= self.begin and t.end <= self.end) \
                    or (t.begin <= self.begin and t.end >= self.end):
                self.source_tags.append(copy(t))

    def add_timex(self, begin, end, timex_type, timex_value):
        self.tarsqi_tags.add_tag('TIMEX3', begin, end,
                                 {'type': timex_type, 'value': timex_value})

    def add_event(self, begin, end, attrs):
        self.tarsqi_tags.add_tag('EVENT', begin, end, attrs)

    def pp(self):
        print "\n", self
        for tag in self.source_tags.tags:
            print "  source_tag  %s" % tag
        for tag in self.tarsqi_tags.tags:
            print "  tarsqi_tag  %s" % tag

    
class TarsqiDocParagraph(TarsqiDocElement):

    def __init__(self, begin, end, text):
        TarsqiDocElement.__init__(self, begin, end, text)

    def is_paragraph():
        return True

    

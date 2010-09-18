
    
class TarsqiDocument:

    """An instance of TarsqiDocument should contain all information that may be needed by the
    wrappers to do their work. It will contain minimal document structure in its elements
    variable. Elements will be typed and include the source string and a dictionary of
    tags. For now we simply use an XmlDocument so we interface easier with the old
    approach.

    Instance Variables:
       docsource - instance of DocSource
       xmldoc - instance of XmlDocument
       elements - list, not yet used
       metadata - a dictionary
       parameters - parameter dcitionary from the Tasqi instance
       
    Note that more variables will be needed. Currently, sseveral wrappers use data from
    the Tarsqi instance, should check what these data are and get them elsewhere,
    potentially by adding them here.

    Also note that now that parameters are available to the wrappers only through this
    class, we do not have access to all the defaults anymore since these were in the
    getopt methods on Tarsqi. Thin k this over."""
    
    def __init__(self, docsource, xmldoc, metadata):
        self.docsource = docsource
        self.xmldoc = xmldoc
        self.elements = []
        self.metadata = metadata
        self.parameters = {}
        
    def add_parameters(self, parameter_dictionary):
        self.parameters = parameter_dictionary
        
    def get_dct(self):
        return self.metadata.get('dct')
    

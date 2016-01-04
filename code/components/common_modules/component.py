"""

Base class for Tarsqi components implemented in Python.

"""


from utilities import logger


class TarsqiComponent:

    """Abstract class for the python components."""
    
    def process(self, infile, outfile):
        """Ask the component to process a file fragment. This is the method that is called
        from the component wrappers and it should be overwritten on all subclasses. An
        error is written to the log file if this method is ever executed."""
        logger.error("TarsqiComponent.process() not overridden")

    def pp_doctree(self, componentName):
        """Print the document tree. Assumes there is a doctree instance variable that
        contains a Document object."""
        print "\n--------- DOCUMENT TREE for %s ----------" % componentName
        self.doctree.pretty_print()

    def pp_xmldoc(self, componentName):
        """Print the XML document."""
        print "\n--------- XmlDocument for %s ----------" % componentName
        self.xmldoc.pretty_print()


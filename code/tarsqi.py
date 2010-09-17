#!/usr/bin/python

"""

Main script that drives all tarsqi toolkit processing.

Low-level and source-specific processing is delegated to the Document Model, which has
access to an XML Parser and metadata processors. The module calls preprocessing and tarsqi
modules to do the real work.

USAGE

   % python tarsqy.py [OPTIONS] INPUT OUTPUT

   INPUT/OUTPUT
   
      Input and output files or directories. If the input is a directory than the output
      directory needs to exist.

   OPTIONS

      --genre=GENRE_NAME
             the genre of the file, None by default
         
      --pipeline=LIST
             comma-separated list of Tarsqi components, defaults to the full pipeline
      
      --perl=PATH
             path to the Perl executable

      --treetagger=PATH
             path to the TreeTagger

      --stanford-parser=PATH
             path to the Stanford parser

      --trap-errors=BOOLEAN
             set error trapping, errors are trapped by default
         
      --loglevel=LEVEL
             set log level to an integer from 0 to 4
      
      --ignore=REGEXP
             determines wat files in a directory are skipped

      All these options can also be set in the settings.txt file. See the manual in
      docs/manual/ for more details on the parameters.

VARIABLES:

   SETTINGS - file with user settings
   COMPONENTS - dictionary with all Tarsqi components
   USE_PROFILER - a boolean determining whether the profiler is used
   PROFILE_OUTPUT - file that profiler statistics are written to

"""

import sys, os, shutil, time, types, getopt

from ttk_path import TTK_ROOT
#from docmodel.initialize import DocumentModelInitializer
from docmodel.source_parser import SourceParser
from docmodel.initialize import create_parser, get_default_pipeline
from utilities import logger
from utilities.file import read_settings
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET
from library.tarsqi_constants import S2T, CLASSIFIER, BLINKER, LINK_MERGER, ARGLINKER

from components.preprocessing.wrapper import PreprocessorWrapper
from components.gutime.wrapper import GUTimeWrapper
from components.evita.wrapper import EvitaWrapper
from components.slinket.wrapper import SlinketWrapper
from components.s2t.wrapper import S2tWrapper
from components.blinker.wrapper import BlinkerWrapper
from components.classifier.wrapper import ClassifierWrapper
from components.merging.wrapper import MergerWrapper
from components.arglinker.wrapper import ArgLinkerWrapper

logger.initialize_logger(os.path.join(TTK_ROOT, 'data', 'logs', 'ttk_log'))

SETTINGS = 'settings.txt'
USE_PROFILER = False
PROFILER_OUTPUT = 'profile.txt'

COMPONENTS = {
    PREPROCESSOR: PreprocessorWrapper,
    GUTIME: GUTimeWrapper,
    EVITA: EvitaWrapper,
    SLINKET: SlinketWrapper,
    S2T: S2tWrapper,
    BLINKER: BlinkerWrapper,
    CLASSIFIER: ClassifierWrapper,
    LINK_MERGER: MergerWrapper,
    ARGLINKER: ArgLinkerWrapper }



class Tarsqi:

    """Main Tarsqi class that drives all processing.

    Instance variables:
        
       parameters - dictionary with processing options
       input - absolute path
       output - absolute path
       basename - basename of input file

       parser
       pipeline
       components

       docsource
       document
       
       DIR_DATA
       DIR_DATA_TMP
       
       document_model - instance of subclass of docmodel.model.DocumentModel 
       metadata - dictionary with metadata
       xml_document - instance of docmodel.xml_parser.XmlDocument
       document - instance of components.common_modules.document.Document

    The first five instance variables are taken from the arguments provided by the user,
    the others are filled in by the document model and later processing. In addition,
    there is a set of instance variables that store directory names and file names for
    intermediate storage of the results of processing components."""


    def __init__(self, opts, input, output):

        """Initialize Tarsqi object conform the data source identifier and the processing
        options. Does not set the instance variables related to the document model and the
        meta data.

        Arguments:
           opts - dictionary of command line options
           input - absolute path
           output - absolute path"""

        # Make sure we're in the right directory. If the toolkit crashed on a previous
        # file it may end up being in a different directory.
        os.chdir(TTK_ROOT)
        
        self.input = input
        self.output = output
        self.basename = _basename(input)
        self.parameters = self._read_parameters(opts)
        if self.parameters.has_key('loglevel'):
            logger.set_level(self.parameters['loglevel'])
        
        self.DIR_DATA = TTK_ROOT + os.sep + 'data'
        self.DIR_DATA_TMP = self.DIR_DATA + os.sep + 'tmp'

        self.components = COMPONENTS
        self.parser = create_parser(self.getopt_genre())
        self.pipeline = self._create_pipeline()
        

    def _create_pipeline(self):
        """Return the pipeline as a list of pairs with the component name and wrapper."""
        component_names = get_default_pipeline(self.getopt_genre())
        if self.getopt_pipeline():
            component_names = self.getopt_pipeline().split(',')
        return [(name, self.components[name]) for name in component_names]
        

    def _read_parameters(self, opts):
        """Initialize options from the settings file and the opts parameter. Loop through
        the options dictionary and replace some of the strings with other objects: replace
        'True' with True, 'False' with False, and strings indicating an integer with that
        integer."""
        parameters = read_settings(SETTINGS)
        for (option, value) in opts:
            parameters[option[2:]] = value
        for (attr, value) in parameters.items():
            if value == 'True'or value == 'False' or value.isdigit():
                parameters[attr] = eval(value)
        return parameters


        
    def process(self):
        
        """Parse the source with source parser and the document parser. Then apply all
        components and write the results to a file. The actual processing itself is driven
        using the processing parameters set at initialization."""

        if self._skip_file(): return
        self._cleanup_directories()
        logger.info("Processing %s" % self.input)
        
        self.docsource = SourceParser().parse_file(self.input)
        self.document = self.parser.parse(self.docsource)

        for (name, wrapper) in self.pipeline[:2]:
            self.apply_component(name, wrapper, self.document)

        self.document.xmldoc.pretty_print()
        
        os.chdir(TTK_ROOT)
        self.write_output()


    def _skip_file(self):
        """Return true if file does not match specified extension. Useful when the script
        is given a directory as input. Probably obsolete, use ignore option instead."""
        extension = self.getopt_extension()
        if not extension: return False
        return self.input.endswith(extension)

    def _cleanup_directories(self):
        """Remove all fragments from the temporary data directory."""
        for file in os.listdir(self.DIR_DATA_TMP):
            if os.path.isfile(self.DIR_DATA_TMP + os.sep + file):
                # sometimes, on linux, weird files show up here, do not delete them
                # should trap these here with an OSError
                if not file.startswith('.'):
                    os.remove(self.DIR_DATA_TMP + os.sep + file)
        

    def apply_component(self, name, wrapper, document):

        """Apply a component if the processing parameters determine that the component
        needs to be applied. This method passes the content tag and the xml_document to
        the wrapper of the component and asks the wrapper to process the document
        fragments.

        Component-level errors are trapped here if trap_errors is True. Those errors are
        now trapped here instead of in the component since we do not tell the component
        what the output file is.

        Arguments:
           name - string, the name of the component
           wrapper - instance of a subclass of ComponentWrapper
           infile - string
           outfile - string

        Return value: None"""

        # NOTE. The wrappers use the xml document and the content tag and then (i) create
        # fragments from the xml doc, (ii) process the fragments, (iii) reinsert the
        # fragments in the xml doc. The code below then writes the xml doc to a file. Most
        # wrappers write the fragments to disk and call the components code on that file,
        # creating a processed fragment again as a disk file. This should be streamlined,
        # too much IO (but alwyas keep the option of printing the file for debugging.

        logger.info("RUNNING " + name)
        print "RUNNING " + name
        if self.getopt_trap_errors():
            try:
                wrapper(document, self).process()
                #self.xml_document.save_to_file(outfile)
            except:
                logger.error(name + " error on " + infile + "\n\t"
                             + str(sys.exc_type) + "\n\t"
                             + str(sys.exc_value) + "\n")
                shutil.copy(infile, outfile)
        else:
            wrapper(document, self).process()
            #document.xml_document.save_to_file(outfile)


    def getopt_genre(self):
        """Return the 'genre' user option. The default is None."""
        return self.parameters.get('genre', None)
        
    def getopt_platform(self):
        """Return the 'platform' user option. The default is None."""
        return self.parameters.get('platform', None)
        
    def getopt_trap_errors(self):
        """Return the 'trap_errors' user option. The default is False."""
        return self.parameters.get('trap_errors', False)

    def getopt_content_tag(self):
        """Return the 'content_tag' user option. The default is None."""
        return self.parameters.get('content_tag', None)

    def getopt_pipeline(self):
        """Return the 'pipeline' user option. The default is None."""
        return self.parameters.get('pipeline', None)

    def getopt_extension(self):
        """Return the 'extension' user option. The default is ''."""
        return self.parameters.get('extension', '')

    def getopt_remove_tags(self):
        """Return the 'remove_tags' user option. The default is True."""
        return self.parameters.get('remove_tags', True)

    def getopt_perl(self):
        """Return the 'perl' user option. The default is 'perl'."""
        return self.parameters.get('perl', 'perl')

    def write_output(self):
        """Write the xml_document to the output file. First inserts the dct from the
        docmodel into the XML document. No arguments, no return value."""
        self.document.xmldoc.save_to_file(self.output)

    def pretty_print(self):
        print self
        print '   metadata    ', self.metadata
        print '   content_tag ', self.content_tag
        print '   document    ', self.xml_document



class TarsqiError(Exception):
    """Tarsqi Exception class, so far only used in this file."""
    pass


def _read_arguments(args):

    """ Read the list of arguments given to the tarsqi.py script.  Return a tuple with
    three elements: processing options dictionary, input path and output path."""

    options = ['genre=', 'trap-errors=', 'pipeline=', 'perl=', 'loglevel=', 'ignore=']

    try:
        (opts, args) = getopt.getopt(sys.argv[1:],'', options)
    except getopt.GetoptError:
        print "ERROR: %s" % sys.exc_value
        sys.exit(_usage_string())
    if len(args) < 2:
        raise TarsqiError("missing input or output arguments\n%s" % _usage_string())
    
    # Use os.path.abspath here because some components change the working directory
    # and when some component fails the cwd may not be reset to the root directory
    input = os.path.abspath(args.pop(0))
    output = os.path.abspath(args.pop(0))
    return (opts, input, output)


def _usage_string():
    return "Usage: % python tarsqi.py [OPTIONS] INPUT OUTPUT\n" + \
           "See tarsqy.py and docs/manual for more details"

def _basename(path):
    basename = os.path.basename(path)
    if basename.endswith('.xml'):
       basename = basename[0:-4]
    return basename

            
def run_tarsqi(args):

    """Main method that is called when the script is executed. It creates a Tarsqi
    instance and lets it process the input. If the input is a directory, this method will
    iterate over the contents, setting up TrasqiControlInstances for all files in the
    directory.

    The arguments are the list of arguments given by the user on the command line. There
    is no return value."""

    (opts, input, output) = _read_arguments(args)

    begin_time = time.time()

    if os.path.isdir(input) and os.path.isdir(output):
        for file in os.listdir(input):
            infile = input + os.sep + file
            outfile = output + os.sep + file
            if os.path.isfile(infile):
                print infile
                Tarsqi(input_type, opts, infile, outfile).process()

    elif os.path.isfile(input):
        if os.path.exists(output):
            raise TarsqiError('output file ' + output + ' already exists')
        Tarsqi(opts, input, output).process()

    else:
        raise TarsqiError('Invalid input and/or output parameters')

    end_time = time.time()
    logger.info("TOTAL PROCESSING TIME: %.3f seconds" % (end_time - begin_time))


def run_profiler(args):

    """Wrap running Tarsqi in the profiler."""

    import profile
    command = "run_tarsqi([%s])" % ','.join(['"'+x+'"' for x in args])
    print 'Running profiler on:', command
    profile.run(command, PROFILER_OUTPUT)


        
    
if __name__ == '__main__':

    try:
        if USE_PROFILER:
            run_profiler(sys.argv[1:])
        else:
            run_tarsqi(sys.argv[1:])
    except TarsqiError:
        sys.exit('ERROR: ' + str(sys.exc_value))

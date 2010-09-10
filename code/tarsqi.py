#!/usr/bin/python

"""

Main script that drives all tarsqi toolkit processing.

Low-level and source-specific processing is delegated to the Document Model, which has
access to an XML Parser and metadata processors. The module calls preprocessing and tarsqi
modules to do the real work.

USAGE

   % python tarsqi.py test
   % python tarsqy.py <INPUT_TYPE> [PROCESSING_FLAGS] <INPUT> <OUTPUT>

   The first way of invoking tarsqi.py runs all the Tarsqi unit tests. The second way runs
   tarsqi over the supplied input.
   
   INPUT_TYPE

      A string that determines the type of the data source, it determines what document
      processor is used and sets a default processing chain.

   PROCESSING_FLAGS

      An optional set of parameters. Can be used to overrule default settings in the
      program as well as default settings given by the INPUT_TYPE. Currently defined flags
      are: trap_errors, log_level, content_tag, and extension. See the manual in
      docs/manual/ for more details on the parameters.

   INPUT/OUTPUT

      Input and output files or directories. If the input is a directory than the output
      directory needs to exist.

Variables:

   USE_PROFILER - a boolean determining whether the profiler is used
   PROFILE_OUTPUT - file that profiler statistics are written to

"""


import sys, os, shutil, time, types

from ttk_path import TTK_ROOT
from docmodel.initialize import DocumentModelInitializer
from utilities import logger
from utilities.file import read_settings
from library.tarsqi_constants import PREPROCESSOR, GUTIME, EVITA, SLINKET
from library.tarsqi_constants import S2T, CLASSIFIER, BLINKER, LINK_MERGER

logger.initialize_logger(os.path.join(TTK_ROOT, 'data', 'logs', 'ttk_log'))

USE_PROFILER = False
PROFILER_OUTPUT = 'profile.txt'


class TarsqiControl:

    """Main Tarsqi class that drives all processing.

    Instance variables:
        
       data_source_identifier - string
       processing_options - dictionary
       input - absolute path
       output - absolute path
       basename - basename of input file
       document_model - instance of subclass of docmodel.model.DocumentModel 
       processing_parameters - instance of docmodel.initialize.ProcessingParameters
       metadata - dictionary with metadata
       xml_document - instance of docmodel.xml_parser.XmlDocument
       document - instance of components.common_modules.document.Document

    The first five instance variables are taken from the arguments provided by the user,
    the others are filled in by the document model and later processing. In addition,
    there is a set of instance variables that store directory names and file names for
    intermediate storage of the results of processing components."""


    def __init__(self, doctype, opts, input, output):

        """Initialize TarsqiControl object conform the data source identifier and the
        processing options. Does not set the instance variables related to the document
        model and the meta data.

        Arguments:
           doctype - data source identifier (string)
           opts - dictionary of processing options
           input - absolute path
           output - absolute path"""

        # Make sure we're in the right directory. If the toolkit crashed on a previous
        # file it may end up being in a different directory.
        os.chdir(TTK_ROOT)
        
        # initialize options from the settings file and the opts parameter
        self.processing_options = read_settings('settings.txt')
        self.processing_options.update(opts)
        _transform_values(self.processing_options)
        
        # user provided options
        self.data_source_identifier = doctype
        self.input = input
        self.output = output
        self.basename = os.path.basename(input)
        if self.basename.endswith('.xml'):
            self.basename = self.basename[0:-4]

        # change log level
        if self.processing_options.has_key('log_level'):
            logger.set_level(self.processing_options['log_level'])
        
        # to be filled in by document model and later processing
        self.document_model = None
        self.processing_parameters = None
        self.metadata = None
        self.xml_document = None
        self.document = None

        # directories and files, user has no control over where
        # intermediate files go
        self.DIR_GUTIME = TTK_ROOT + os.sep + 'gutime'
        self.DIR_DATA = TTK_ROOT + os.sep + 'data'
        self.DIR_DATA_TMP = self.DIR_DATA + os.sep + 'tmp'
        self.FILE_PRE = self.DIR_DATA_TMP + os.sep + self.basename + '.pre.xml'
        self.FILE_GUT = self.DIR_DATA_TMP + os.sep + self.basename + '.gut.xml'
        self.FILE_EVI = self.DIR_DATA_TMP + os.sep + self.basename + '.evi.xml'
        self.FILE_SLI = self.DIR_DATA_TMP + os.sep + self.basename + '.sli.xml'
        self.FILE_S2T = self.DIR_DATA_TMP + os.sep + self.basename + '.s2t.xml'
        self.FILE_BLI = self.DIR_DATA_TMP + os.sep + self.basename + '.bli.xml'
        self.FILE_CLA = self.DIR_DATA_TMP + os.sep + self.basename + '.cla.xml'
        self.FILE_MER = self.DIR_DATA_TMP + os.sep + self.basename + '.mer.xml'
        self.FILE_ARG = self.DIR_DATA_TMP + os.sep + self.basename + '.arg.xml'


    def process(self):

        """Method called after initialization. Sets up the document model, reads the
        input, applies all components, and writes the results to a file.  Only define
        high-level scaffolding for processing task, the actual processing itself is driven
        using the processing parameters set at initialization and the code that applies a
        component is responsible for determining whether the component is needed.

        This method takes no arguments and has no return value."""

        # do nothing if file does not match specified extension, used
        # when the script is given a directory as input
        extension = self.getopt_extension()
        if not self.input.endswith(extension):
            return

        self.cleanup_directories()
        logger.info("Processing %s" % self.input)
        self.setup_docmodel()
        self.read_input()
        for pipeline_element in self.processing_parameters.pipeline:
            (name, wrapper, infile, outfile) = pipeline_element
            self.apply_component(name, wrapper, infile, outfile)
        os.chdir(TTK_ROOT)
        self.write_output()
        #self.pretty_print()
        #self.xml_document.pretty_print()
        

    def cleanup_directories(self):
        """Remove all fragments from the temporary data directory."""
        for file in os.listdir(self.DIR_DATA_TMP):
            if os.path.isfile(self.DIR_DATA_TMP + os.sep + file):
                # sometimes, on linux, weird files show up here, do not delete them
                # should trap these here with an OSError
                if not file.startswith('.'):
                    os.remove(self.DIR_DATA_TMP + os.sep + file)
        
    def setup_docmodel(self):
        """Create a document model using the data_source_identifier field and the
        processing options. Variation in document processing is driven by the document
        model, once it is set, all steps are the same from the perspective of
        TarsqControl."""
        DocumentModelInitializer().setup_docmodel(self)
        
    def read_input(self):
        """Ask the document model to read the document, which involves creating an
        instance of XmlDocument and parsing the meta data. The XML document and the
        metadata are then retrieved from the document model and put in the xml_document
        and metadata variables. No arguments and no return value."""
        self.document_model.read_document()
        self.xml_document = self.document_model.get_xml_document()
        self.metadata = self.document_model.get_metadata()


    def apply_component(self, name, wrapper, infile, outfile):

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

        logger.info("RUNNING " + name + " on: " + infile)
        if self.getopt_trap_errors():
            try:
                wrapper(self.content_tag, self.xml_document, self).process()
                self.xml_document.save_to_file(outfile)
            except:
                logger.error(name + " error on " + infile + "\n\t"
                             + str(sys.exc_type) + "\n\t"
                             + str(sys.exc_value) + "\n")
                shutil.copy(infile, outfile)
        else:
            wrapper(self.content_tag, self.xml_document, self).process()
            self.xml_document.save_to_file(outfile)


    def getopt_platform(self):
        """Return the 'platform' user option. The default is None."""
        return self.processing_options.get('platform', None)
        
    def getopt_trap_errors(self):
        """Return the 'trap_errors' user option. The default is False."""
        return self.processing_options.get('trap_errors', False)

    def getopt_content_tag(self):
        """Return the 'content_tag' user option. The default is None."""
        return self.processing_options.get('content_tag', None)

    def getopt_pipeline(self):
        """Return the 'pipeline' user option. The default is None."""
        return self.processing_options.get('pipeline', None)

    def getopt_extension(self):
        """Return the 'extension' user option. The default is ''."""
        return self.processing_options.get('extension', '')

    def getopt_remove_tags(self):
        """Return the 'remove_tags' user option. The default is True."""
        return self.processing_options.get('remove_tags', True)

    def getopt_perl(self):
        """Return the 'perl' user option. The default is 'perl'."""
        return self.processing_options.get('perl', 'perl')

    def write_output(self):
        """Write the xml_document to the output file. First inserts the dct
        from the docmodel into the XML documentNo arguments and no
        return value."""
        #self.xml_document.insert_dct(self.document_model.get_dct(),
        #                             self.document_model.get_content_tag())
        self.xml_document.save_to_file(self.output)


    def pretty_print(self):
        """Pretty printer that prints to the console. Example output:

        <__main__.TarsqiControl instance at 0x6b40a8>
           metadata     {'dct': u'19980108'}
           parameters   <docmodel.initialize.ProcessingParameters instance at 0x6b4120>
           content_tag  TEXT
           document     <docmodel.xml_parser.XmlDocument instance at 0x6b4170>"""

        print self
        print '   metadata    ', self.metadata
        print '   parameters  ', self.processing_parameters
        print '   content_tag ', self.content_tag
        print '   document    ', self.xml_document


def read_arguments(args):

    """ Reads the list of arguments given to the tarsqi.py script.  Returns a tuple with
    four elements: data source identifier, processing options dictionary, input path and
    output path."""

    if len(args) < 3:
        sys.exit('ERROR: missing arguments')
    data_source_identifier = args.pop(0)
    processing_options = {}
    while args and '=' in args[0]:
        flag = args.pop(0)
        (option, value) = flag.split('=', 2)
        processing_options[option] = value
    # Use os.path.abspath here because some components change the
    # working directory and when some component fails the cwd may
    # not be reset to the root directory
    if len(args) < 2:
        sys.exit('ERROR: missing arguments')
    input = os.path.abspath(args.pop(0))
    output = os.path.abspath(args.pop(0))
    return (data_source_identifier, processing_options, input, output)


def _transform_values(dict):

    """Loops through a directory where all the values are strings and replaces some of
    them with other objects. Replaces 'True' with True, 'False' with False, and strings
    indicating an integer with that integer."""

    for (attr, value) in dict.items():
        if type(value) != types.StringType:
            continue
        if value == 'True'or value == 'False' or value.isdigit():
            dict[attr] = eval(value)

    
def run_tarsqi(args):

    """Main method that is called when the script is executed. It creates a TarsqiControl
    instance and lets it process the input. If the input is a directory, this method will
    iterate over the contents, setting up TrasqiControlInstances for all files in the
    directory.

    The arguments are the list of arguments given by the user on the command line. There
    is no return value."""

    (input_type, opts, input, output) = read_arguments(args)

    begin_time = time.time()

    if os.path.isdir(input) and os.path.isdir(output):
        for file in os.listdir(input):
            infile = input + os.sep + file
            outfile = output + os.sep + file
            if os.path.isfile(infile):
                print infile
                TarsqiControl(input_type, opts, infile, outfile).process()

    elif os.path.isfile(input):
        if os.path.exists(output):
            sys.exit('ERROR: output file ' + output + ' already exists')
        TarsqiControl(input_type, opts, input, output).process()

    else:
        sys.exit('Invalid input and/or output parameters')

    end_time = time.time()
    logger.info("TOTAL PROCESSING TIME: %.3f seconds" % (end_time - begin_time))


def run_profiler(args):
    """Wrap running Tarsqi in the profiler. The problem is that this currently fails for
     unknown reasons. It runs through all the tarsqi components but then it breaks."""
    import profile
    args = ','.join( map(lambda x: '"'+x+'"',args) )
    command = "run_tarsqi([%s])" % args
    print 'Running profiler on:', command
    profile.run(command, PROFILER_OUTPUT)



if __name__ == '__main__':
    if USE_PROFILER:
        run_profiler(sys.argv[1:])
    else:
        run_tarsqi(sys.argv[1:])

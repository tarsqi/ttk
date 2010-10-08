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

import sys, os, time, types, getopt

from ttk_path import TTK_ROOT
from components import COMPONENTS
from docmodel.source_parser import SourceParser
from docmodel.main import create_parser, get_default_pipeline
from mixins.parameters import ParameterMixin
from utilities import logger
from utilities.file import read_settings

logger.initialize_logger(os.path.join(TTK_ROOT, 'data', 'logs', 'ttk_log'), level=3)

SETTINGS = 'settings.txt'
USE_PROFILER = False
PROFILER_OUTPUT = 'profile.txt'


class Tarsqi(ParameterMixin):

    """Main Tarsqi class that drives all processing.

    Instance variables:
        
       input - absolute path
       output - absolute path
       basename - basename of input file
       parameters - dictionary with processing options

       parser - a genre-specific document parsers
       pipeline - list of name-wrapper pairs
       components - dictionary of components

       docsource - instance of DocSource
       document - instance of TarsqiDocument
       
       DIR_TMP_DATA - path
       
    The first seven instance variables are initialized using the arguments provided by the
    user, docsource and document are filled in during processing."""


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
        
        self.DIR_TMP_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')

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
        using the processing parameters set at initialization. Each component is given the
        TarsqiDocument and updates it."""

        if self._skip_file(): return
        self._cleanup_directories()
        logger.info("Processing %s" % self.input)
        
        self.docsource = SourceParser().parse_file(self.input)
        self.document = self.parser.parse(self.docsource)
        self.document.add_parameters(self.parameters)

        # testing whether docsource can be printed
        #self.docsource.print_xml('tmp.xml')

        for (name, wrapper) in self.pipeline:
            print name
            self.apply_component(name, wrapper, self.document)

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
        for file in os.listdir(self.DIR_TMP_DATA):
            if os.path.isfile(self.DIR_TMP_DATA + os.sep + file):
                # sometimes, on linux, weird files show up here, do not delete them
                # should trap these here with an OSError
                if not file.startswith('.'):
                    os.remove(self.DIR_TMP_DATA + os.sep + file)
        

    def apply_component(self, name, wrapper, document):

        """Apply a component if the processing parameters determine that the component
        needs to be applied. This method passes the TarsqDocument instance to
        the component wrapper.

        Component-level errors are trapped here if trap_errors is True. Those errors are
        now trapped here instead of in the component since we do not tell the component
        what the output file is.

        Arguments:
           name - string, the name of the component
           wrapper - instance of one of the wrapper classes
           document - instance of TarsqiDocument
        Return value: None

        Wrappers are now only given a TarsqiDocument, which includes the parameters from
        teh Tarsqi instance. May in the future need to add some kind of dictionary with
        other needed info."""

        logger.info(name + '............')
        t1 = time.time()
        if self.getopt_trap_errors():
            try:
                wrapper(document).process()
            except:
                logger.error(name + " error on " + infile + "\n\t"
                             + str(sys.exc_type) + "\n\t"
                             + str(sys.exc_value) + "\n")
                # TODO: revisit this since we do not have infile and outfile anymore, does
                # the TarsqiDocument need to be reset?
                #shutil.copy(infile, outfile)
        else:
            wrapper(document).process()
        logger.info("%s DONE (%.3f seconds)" % (name, time.time() - t1))


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
                Tarsqi(opts, infile, outfile).process()

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

#!/usr/bin/python

"""

Main script that drives all tarsqi toolkit processing.

Low-level and source-specific processing is delegated to the docmodel package, which has
access to an XML Parser and metadata processors. This script calls on preprocessing and
tarsqi modules to do the real work.

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

scriptPath = os.path.abspath(__file__)
TTK_ROOT = os.path.dirname(scriptPath)
os.environ['TTK_ROOT'] = TTK_ROOT

# TODO: need to get rid of this by recompiling all FSA's, this is done for Evita
# and removing the line below does not hurt Evita anymore, but Slinket patterns
# still need to be recompiled
sys.path[1:1] = [ os.path.join(TTK_ROOT, 'utilities') ]

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
        
       input         -  absolute path
       output        -  absolute path
       basename      -  basename of input file
       parameters    -  dictionary with processing options
       parser        -  a genre-specific document parsers
       pipeline      -  list of name-wrapper pairs
       components    -  dictionary of components
       docsource     -  instance of DocSource
       document      -  instance of TarsqiDocument
       DIR_TMP_DATA  -  path
       
    The first seven instance variables are initialized using the arguments provided by the
    user, docsource and document are filled in during processing."""


    def __init__(self, opts, infile, outfile):

        """Initialize Tarsqi object conform the data source identifier and the processing
        options. Does not set the instance variables related to the document model and the
        meta data. Arguments:
           opts - dictionary of command line options
           input - absolute path
           output - absolute path"""

        # Make sure we're in the right directory. If the toolkit crashed on a previous
        # file it may end up being in a different directory.
        os.chdir(TTK_ROOT)

        self.input = infile
        self.output = outfile
        self.basename = _basename(infile) if infile else None
        self.parameters = self._read_parameters(opts)
        if self.parameters.has_key('loglevel'):
            logger.set_level(self.parameters['loglevel'])
        
        self.DIR_TMP_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')

        self.components = COMPONENTS
        self.parser = create_parser(self.getopt_genre(), self.parameters)
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
            if value == 'True' or value == 'False' or value.isdigit():
                parameters[attr] = eval(value)
        return parameters

    def process(self):
        """Parse the source with source parser and the document parser. Then apply all
        components and write the results to a file. The actual processing itself is driven
        using the processing parameters set at initialization. Each component is given the
        TarsqiDocument and updates it."""
        if self._skip_file(): return
        self._cleanup_directories()
        logger.info(self.input)
        self.docsource = SourceParser().parse_file(self.input)
        self.document = self.parser.parse(self.docsource)
        self.document.add_parameters(self.parameters)
        for (name, wrapper) in self.pipeline:
            self.apply_component(name, wrapper, self.document)
        os.chdir(TTK_ROOT)
        self.write_output()

    def process_string(self, input_string):
        """Parse the input string with source parser and create a TarsqiDocument
        with the document parser. Then the processing itself is driven by the
        processing parameters set at initialization. Each component is given the
        TarsqiDocument and updates it. Returns the TarsqiDocument instance."""
        logger.info(input_string)
        self.docsource = SourceParser().parse_string(input_string)
        self.document = self.parser.parse(self.docsource)
        self.document.add_parameters(self.parameters)
        for (name, wrapper) in self.pipeline:
            self.apply_component(name, wrapper, self.document)
        return self.document

    def _skip_file(self):
        """Return true if file does not match specified extension. Useful when
        the script is given a directory as input. Probably obsolete, use ignore
        option instead."""
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

    def apply_component(self, name, wrapper, tarsqidocument):
        """Apply a component by taking the TarsqDocument, which includes the
        parameters from the Tarsqi instance, and passing it to the component
        wrapper. Component-level errors are trapped here if --trap-errors is
        True. If errors are trapped, it is still possible that partial results
        were written to the TagRepositories in the TarsqiDocument."""
        logger.info(name + '............')
        t1 = time.time()
        if self.getopt_trap_errors():
            try:
                wrapper(tarsqidocument).process()
            except:
                print  "%s error:\n\t%s\n\t%s\n" \
                    % (name, sys.exc_type, sys.exc_value)
        else:
            wrapper(tarsqidocument).process()
        logger.info("%s DONE (%.3f seconds)" % (name, time.time() - t1))

    def write_output(self):
        """Write the TarsqiDocument to the output file."""
        try:
            self.document.print_all(self.output)
        except:
            print "ERROR printing output"

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
    options = ['genre=', 'pipeline=', 'trap-errors=', 'content_tag=', 'perl=',
               'loglevel=', 'ignore=', 'platform=', 'treetagger=']
    try:
        (opts, args) = getopt.getopt(args,'', options)
        return (opts, args)
    except getopt.GetoptError:
        print "ERROR: %s" % sys.exc_value
        sys.exit(_usage_string())

def _usage_string():
    return "Usage: % python tarsqi.py [OPTIONS] INPUT OUTPUT\n" + \
           "See tarsqy.py and docs/manual for more details"

def _basename(path):
    basename = os.path.basename(path)
    if basename.endswith('.xml'):
       basename = basename[0:-4]
    return basename
            
def run_tarsqi(args):
    """Main method that is called when the script is executed from the command
    line. It creates a Tarsqi instance and lets it process the input. If the
    input is a directory, this method will iterate over the contents, setting up
    TrasqiControlInstances for all files in the directory. The arguments are the
    list of arguments given by the user on the command line. There is no return
    value."""
    (opts, args) = _read_arguments(args)
    if len(args) < 2:
        raise TarsqiError("missing input or output arguments\n%s" % _usage_string())
    # Use os.path.abspath here because some components change the working directory
    # and when some component fails the cwd may not be reset to the root directory
    inpath = os.path.abspath(args[0])
    outpath = os.path.abspath(args[1])
    t0 = time.time()
    if os.path.isdir(inpath) and os.path.isdir(outpath):
        for file in os.listdir(inpath):
            infile = inpath + os.sep + file
            outfile = outpath + os.sep + file
            if os.path.isfile(infile):
                print infile
                Tarsqi(opts, infile, outfile).process()
    elif os.path.isfile(inpath):
        if os.path.exists(outpath):
            raise TarsqiError('output file ' + outpath + ' already exists')
        Tarsqi(opts, inpath, outpath).process()
    else:
        raise TarsqiError('Invalid input and/or output parameters')
    logger.info("TOTAL PROCESSING TIME: %.3f seconds" % (time.time() - t0))


def run_profiler(args):
    """Wrap running Tarsqi in the profiler."""
    import profile
    command = "run_tarsqi([%s])" % ','.join(['"'+x+'"' for x in args])
    print 'Running profiler on:', command
    profile.run(command, PROFILER_OUTPUT)

def test():
    os.remove('out.xml')
    run_tarsqi(['--pipeline=PREPROCESSOR,GUTIME,EVITA',
                'data/in/simple-xml/tiny.xml',
                'out.xml'])

def process_string(text, pipeline='PREPROCESSOR', loglevel=2, trap_errors=False):
    """Run tarsqi on a bare string without any XML tags, handing in pipeline,
    loglevel and error trapping options."""
    (opts, args) = _read_arguments(["--pipeline=%s" % pipeline,
                                    "--loglevel=%s" % loglevel,
                                    "--trap-errors=%s" % trap_errors])
    tarsqi = Tarsqi(opts, None, None)
    return tarsqi.process_string("<TEXT>%s</TEXT>" % text)


if __name__ == '__main__':
    try:
        if USE_PROFILER:
            run_profiler(sys.argv[1:])
        else:
            run_tarsqi(sys.argv[1:])
    except TarsqiError:
        sys.exit('ERROR: ' + str(sys.exc_value))

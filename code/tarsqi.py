#!/usr/bin/python

"""Main script that drives all tarsqi toolkit processing.

Source-specific processing is delegated to the docmodel package, which has
access to source parsers and metadata parsers. This script also calls on
various tarsqi modules to do the rest of the real work.

USAGE

   % python tarsqy.py [OPTIONS] INPUT OUTPUT

   INPUT/OUTPUT

      Input and output files or directories. If the input is a directory than
      the output directory needs to exist.

   OPTIONS

      --genre=GENRE_NAME
             the genre of the file, None by default; this would in the future
             distinguish between genres or domains like newswire, historical,
             medial etcetera, but it is not yet used

      --source=SOURCE_NAME
             the source of the file; this reflects the source type of the
             document and allows components, especially the source parser,
             metadata parser and document structure parser, to be sensitive to
             idiosyncratic properties of the text (for example, location of the
             DCT and the format of the text); xml by default, other source types
             are text and ttk

      --pipeline=LIST
             comma-separated list of Tarsqi components, defaults to the full
             pipeline

      --perl=PATH
             path to the Perl executable

      --treetagger=PATH
             path to the TreeTagger

      --mallet
             Location of Mallet, this should be the directory that contains the
             bin directory

      --classifier
             The classifier used by the Mallet classifier, the default is MaxEnt

      --ee-model
             The model used for classifying event-event tlinks, this is a model
             file in components/classifier/models, the default is set to
             tb-vectors.ee.model

      --et-model
             The model used for classifying event-timex tlinks, this is a model
             file in components/classifier/models, the default is set to
             tb-vectors.et.model

      --trap-errors=BOOLEAN
             set error trapping, errors are trapped by default

      --loglevel=LEVEL
             set log level to an integer from 0 to 4, the higher the level the
             more messages will be written to the log, see utilities.logger for
             more details

      All these options can also be set in the settings.txt file. See the manual
      in docs/manual/ for more details on the parameters.

VARIABLES:

   SETTINGS - file with user settings
   COMPONENTS - dictionary with all Tarsqi components
   USE_PROFILER - a boolean determining whether the profiler is used
   PROFILE_OUTPUT - file that profiler statistics are written to

"""

import sys, os, time, types, getopt

import root
from components import COMPONENTS
from docmodel.main import get_default_pipeline
from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser
from utilities import logger
from utilities.file import read_settings

TTK_ROOT = os.environ['TTK_ROOT']
SETTINGS = os.path.join(TTK_ROOT, 'settings.txt')
USE_PROFILER = False
PROFILER_OUTPUT = 'profile.txt'

logger.initialize_logger(os.path.join(TTK_ROOT, 'data', 'logs', 'ttk_log'),
                         level=3)


class Tarsqi:

    """Main Tarsqi class that drives all processing.

    Instance variables:

       input                -  absolute path
       output               -  absolute path
       basename             -  basename of input file
       options              -  an instance of Options with processing options
       source_parser        -  a source-specific parser for the source
       metadata_parser      -  a source-specific metadata parser
       docstructure_parser  -  a document structure parser
       pipeline             -  list of name-wrapper pairs
       components           -  dictionary of components
       document             -  instance of TarsqiDocument
       DIR_TMP_DATA         -  path for temporary files

    The first nine instance variables are initialized using the arguments
    provided by the user, document is initialized and changed during
    processing."""

    def __init__(self, opts, infile, outfile):
        """Initialize Tarsqi object conform the data source identifier and the
        processing options. Does not set the instance variables related to the
        document model and the meta data. The opts argument has a list of
        commanid line options and the infile and outfile arguments are typically
        absolute paths, but they can be None when we are processing strings."""
        # Make sure we're in the right directory. If the toolkit crashed on a
        # previous file we may be in a different directory.
        os.chdir(TTK_ROOT)
        self.input = infile
        self.output = outfile
        self.basename = _basename(infile) if infile else None
        self.options = Options(opts)
        if self.options.loglevel:
            logger.set_level(self.options.loglevel)
        self.DIR_TMP_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')
        self.components = COMPONENTS
        self.source_parser = create_source_parser(self.options)
        self.metadata_parser = create_metadata_parser(self.options)
        self.docstructure_parser = create_docstructure_parser()
        self.pipeline = self._create_pipeline()

    def process(self):
        """Parse the source with the source parser, the metadata parser and the
        document structure parser, apply all components and write the results to
        a file. The actual processing itself is driven using the processing
        options set at initialization. Components are given the TarsqiDocument
        and update it."""
        if not self._skip_file():
            self._cleanup_directories()
            logger.info(self.input)
            self.document = self.source_parser.parse_file(self.input)
            self._process_document()
            self._write_output()

    def process_string(self, input_string):
        """Similar to process(), except that it runs on an input string and not
        on a file, it does not write the output to a file and it returns the
        TarsqiDocument."""
        logger.info(input_string)
        self.document = self.source_parser.parse_string(input_string)
        self._process_document()
        return self.document

    def _process_document(self):
        """Process the document by running the metadata parser, the document
        structure parser and the pipeline components."""
        self.metadata_parser.parse(self.document)
        self.docstructure_parser.parse(self.document)
        self.document.add_options(self.options)
        for (name, wrapper) in self.pipeline:
            self._apply_component(name, wrapper, self.document)

    def _skip_file(self):
        """Return true if file does not match specified extension. Useful when
        the script is given a directory as input. Probably obsolete, use ignore
        option instead."""
        extension = self.options.extension
        if not extension:
            return False
        return self.input.endswith(extension)

    def _cleanup_directories(self):
        """Remove all fragments from the temporary data directory."""
        for file in os.listdir(self.DIR_TMP_DATA):
            if os.path.isfile(self.DIR_TMP_DATA + os.sep + file):
                # sometimes, on linux, weird files show up here, do not delete
                # them should trap these here with an OSError
                if not file.startswith('.'):
                    os.remove(self.DIR_TMP_DATA + os.sep + file)

    def _apply_component(self, name, wrapper, tarsqidocument):
        """Apply a component by taking the TarsqDocument, which includes the
        options from the Tarsqi instance, and passing it to the component
        wrapper. Component-level errors are trapped here if --trap-errors is
        True. If errors are trapped, it is still possible that partial results
        were written to the TagRepositories in the TarsqiDocument."""
        logger.info(name + '............')
        t1 = time.time()
        if self.options.trap_errors:
            try:
                wrapper(tarsqidocument).process()
            except:
                logger.error("%s error:\n\t%s\n\t%s\n"
                             % (name, sys.exc_type, sys.exc_value))
        else:
            wrapper(tarsqidocument).process()
        logger.info("%s DONE (%.3f seconds)" % (name, time.time() - t1))

    def _create_pipeline(self):
        """Return the pipeline as a list of pairs with the component name and
        wrapper."""
        component_names = get_default_pipeline(self.options)
        if self.options.pipeline:
            component_names = self.options.pipeline.split(',')
        return [(name, self.components[name]) for name in component_names]

    def _write_output(self):
        """Write the TarsqiDocument to the output file."""
        if self.options.trap_errors:
            try:
                self.document.print_all(self.output)
            except:
                print "ERROR printing output"
        else:
            self.document.print_all(self.output)

    def pretty_print(self):
        print self
        print '   metadata    ', self.metadata
        print '   content_tag ', self.content_tag
        print '   document    ', self.xml_document


class Options:

    """A dictionary to keep track of all the options. Options are stored in a
    dictionary, but are also accessable directly through instance variables."""

    def __init__(self, options):
        """Initialize options from the settings file and the opts parameter.
        Loop through the options dictionary and replace some of the strings with
        other objects: replace 'True' with True, 'False' with False, and strings
        indicating an integer with that integer."""
        self._options = read_settings(SETTINGS)
        for (option, value) in options:
            self._options[option[2:]] = value
        for (attr, value) in self._options.items():
            if value in ('True', 'False') or value.isdigit():
                self._options[attr] = eval(value)
        self.genre = self.getopt('genre')
        self.source = self.getopt('source')
        self.platform = self.getopt('platform')
        self.pipeline = self.getopt('pipeline')
        self.loglevel = self.getopt('loglevel')
        self.trap_errors = self.getopt('trap-errors', True)
        self.extension = self.getopt('extension', '')
        self.perl = self.getopt('perl', 'perl')
        self.mallet = self.getopt('mallet')
        self.treetagger = self.getopt('treetagger')
        self.classifier = self.getopt('classifier')
        self.ee_model = self.getopt('ee-model')
        self.et_model = self.getopt('et-model')

    def __str__(self):
        return str(self._options)

    def __getitem__(self, key):
        return self._options[key]

    def items(self):
        # TODO: there must be a better way to do this dictionary emulation
        return self._options.items()

    def getopt(self, option_name, default=None):
        """Return the option, use None as default."""
        return self._options.get(option_name, default)


class TarsqiError(Exception):
    """Tarsqi Exception class, so far only used in this file."""
    pass


def _read_arguments(args):
    """ Read the list of arguments given to the tarsqi.py script.  Return a
    tuple with three elements: processing options dictionary, input path and
    output path."""
    options = ['genre=', 'source=', 'pipeline=', 'trap-errors=',
               'perl=', 'loglevel=', 'platform=', 'treetagger=',
               'mallet=', 'classifier=', 'ee-model=', 'et-model=']
    try:
        (opts, args) = getopt.getopt(args, '', options)
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
        raise TarsqiError("missing input or output arguments\n%s"
                          % _usage_string())
    # Use os.path.abspath here because some components change the working
    # directory and when some component fails the cwd may not be reset to the
    # root directory
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
        raise TarsqiError('Invalid input and/or output options')
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

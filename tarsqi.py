"""tarsqi.py

Main script that drives all tarsqi toolkit processing.

Source-specific processing is delegated to the docmodel package, which has
access to source parsers and metadata parsers. This script also calls on
various tarsqi modules to do the rest of the real work.


USAGE

   % python tarsqy.py [OPTIONS] INPUT OUTPUT

   INPUT/OUTPUT

      Input and output files or directories. If the input is a directory than
      the output directory needs to exist.

   OPTIONS

      --source SOURCE_NAME
          The source of the file; this reflects the source type of the document
          and allows components, especially the source parser and the metadata
          parser, to be sensitive to idiosyncratic properties of the text (for
          example, the location of the DCT and the format of the text). The
          source type is xml by default, other general source types are text and
          ttk. There are four more types that can be used to process the more
          specific sample data in data/in: timebank for data/in/TimeBank, atee
          for data/in/ATEE, rte3 for data/in/RTE3 and db for data/in/db.

      --pipeline LIST
          Comma-separated list of Tarsqi components, defaults to the full
          pipeline.

      --perl PATH
          Path to the Perl executable. Typically the operating system default is
          fine here and this options does not need to be used.

      --treetagger PATH
          Path to the TreeTagger.

      --mallet PATH
          Location of Mallet, this should be the directory that contains the
          bin directory.

      --classifier STRING
          The classifier used by the Mallet classifier, the default is MaxEnt.

      --ee-model FILENAME
          The model used for classifying event-event tlinks, this is a model
          file in components/classifier/models, the default is set to
          tb-vectors.ee.model.

      --et-model FILENAME
          The model used for classifying event-timex tlinks, this is a model
          file in components/classifier/models, the default is set to
          tb-vectors.et.model.

      --trap-errors True|False
          Set error trapping, errors are trapped by default.

      --loglevel INTEGER
          Set log level to an integer from 0 to 4, the higher the level the
          more messages will be written to the log, see utilities.logger for
          more details.

      All these options can also be set in the config.txt file.


VARIABLES:

   TTK_ROOT - the TTK directory
   CONFIG - file with user settings
   COMPONENTS - dictionary with all Tarsqi components
   USE_PROFILER - a boolean determining whether the profiler is used
   PROFILER_OUTPUT - file that profiler statistics are written to

"""

import sys, os, time, types, getopt

import root
from components import COMPONENTS
from docmodel.document import TarsqiDocument
from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser
from utilities import logger
from utilities.file import read_config

TTK_ROOT = os.environ['TTK_ROOT']
CONFIG = os.path.join(TTK_ROOT, 'config.txt')
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
       tarsqidoc            -  an instance of TarsqiDocument
       source_parser        -  a source-specific parser for the source
       metadata_parser      -  a source-specific metadata parser
       docstructure_parser  -  a document structure parser
       pipeline             -  list of name-wrapper pairs
       components           -  dictionary of Tarsqi components
       document             -  instance of TarsqiDocument
       tmp_data             -  path to directory for temporary files

    The first nine instance variables are initialized using the arguments
    provided by the user, the document variable is initialized and changed
    during processing. """

    def __init__(self, opts, infile, outfile):
        """Initialize Tarsqi object conform the data source identifier and the
        processing options. Does not set the instance variables related to the
        document model and the meta data. The opts argument has a list of
        command line options and the infile and outfile arguments are typically
        absolute paths, but they can be None when we are processing strings."""
        _set_working_directory()
        self.input = infile
        self.output = outfile
        self.basename = _basename(infile) if infile else None
        self.options = Options(opts)
        self.tarsqidoc = TarsqiDocument()
        self.tarsqidoc.add_options(self.options)
        if self.options.loglevel:
            logger.set_level(self.options.loglevel)
        self.tmp_data = os.path.join(TTK_ROOT, 'data', 'tmp')
        self.components = COMPONENTS
        self.source_parser = create_source_parser(self.options)
        self.metadata_parser = create_metadata_parser(self.options)
        self.docstructure_parser = create_docstructure_parser()
        self.pipeline = self._create_pipeline()

    def process_document(self):
        """Parse the source with the source parser, the metadata parser and the
        document structure parser, apply all components and write the results to
        a file. The actual processing itself is driven using the processing
        options set at initialization. Components are given the TarsqiDocument
        and update it."""
        self._cleanup_directories()
        logger.info(self.input)
        self.source_parser.parse_file(self.input, self.tarsqidoc)
        self.metadata_parser.parse(self.tarsqidoc)
        self.docstructure_parser.parse(self.tarsqidoc)
        for (name, wrapper) in self.pipeline:
            self._apply_component(name, wrapper, self.tarsqidoc)
        self._write_output()

    def process_string(self, input_string):
        """Similar to process(), except that it runs on an input string and not
        on a file, it does not write the output to a file and it returns the
        TarsqiDocument."""
        logger.info(input_string)
        self.source_parser.parse_string(input_string, self.tarsqidoc)
        self.metadata_parser.parse(self.tarsqidoc)
        self.docstructure_parser.parse(self.tarsqidoc)
        for (name, wrapper) in self.pipeline:
            self._apply_component(name, wrapper, self.tarsqidoc)
        return self.tarsqidoc

    def _cleanup_directories(self):
        """Remove all fragments from the temporary data directory."""
        for file in os.listdir(self.tmp_data):
            if os.path.isfile(self.tmp_data + os.sep + file):
                # sometimes, on linux, weird files show up here, do not delete
                # them should trap these here with an OSError
                if not file.startswith('.'):
                    os.remove(self.tmp_data + os.sep + file)

    def _apply_component(self, name, wrapper, tarsqidocument):
        """Apply a component by taking the TarsqDocument, which includes the
        options from the Tarsqi instance, and passing it to the component
        wrapper. Component-level errors are trapped here if --trap-errors is
        True. If errors are trapped, it is still possible that partial results
        were written to the TagRepositories in the TarsqiDocument."""
        logger.info(name + '............')
        t1 = time.time()
        if self.options.trap_errors:
            try: wrapper(tarsqidocument).process()
            except: _log_error(name)
        else:
            wrapper(tarsqidocument).process()
        logger.info("%s DONE (%.3f seconds)" % (name, time.time() - t1))

    def _create_pipeline(self):
        """Return the pipeline as a list of pairs with the component name and
        wrapper."""
        component_names = self.options.pipeline.split(',')
        return [(name, self.components[name]) for name in component_names]

    def _write_output(self):
        """Write the TarsqiDocument to the output file."""
        if self.options.trap_errors:
            try:
                self.tarsqidoc.print_all(self.output)
            except:
                print "ERROR printing output"
        else:
            self.tarsqidoc.print_all(self.output)

    def pretty_print(self):
        print self
        print '   metadata    ', self.metadata
        print '   content_tag ', self.content_tag
        print '   document    ', self.xml_document


class Options():

    """A class to keep track of all the options. Options can be accessed with the
    getopt() method, but standard options are also accessable directly through
    the following instance variables: source, pipeline, loglevel, trap_errors,
    perl, treetagger, mallet, classifier, ee_model and et_model. There is no
    instance variable access for user-defined options in the config.txt file."""

    def __init__(self, options):
        """Initialize options from the config file and the options handed in to the
        tarsqi script."""
        self._read_options(CONFIG, options)
        self._massage_options()
        # put options in instance variables for convenience, this is not done
        # for those options from config.txt that are user-specific
        self.source = self.getopt('source')
        self.pipeline = self.getopt('pipeline')
        self.loglevel = self.getopt('loglevel')
        self.trap_errors = self.getopt('trap-errors', True)
        self.perl = self.getopt('perl', 'perl')
        self.mallet = self.getopt('mallet')
        self.treetagger = self.getopt('treetagger')
        self.classifier = self.getopt('classifier')
        self.ee_model = self.getopt('ee-model')
        self.et_model = self.getopt('et-model')

    def _read_options(self, CONFIG, options):
        """Read options from config file and command line options."""
        self._options = read_config(CONFIG)
        for (option, value) in options:
            self._options[option[2:]] = value

    def _massage_options(self):
        """Loop through the options dictionary and replace some of the strings
        with other objects: replace 'True' with True, 'False' with False, and
        strings indicating an integer with that integer. Also, for the --mallet
        and --treetagger options, which are known to be paths, replace the value
        with the absolute path."""
        for (attr, value) in self._options.items():
            if value in ('True', 'False') or value.isdigit():
                self._options[attr] = eval(value)
            elif attr in ('mallet', 'treetagger'):
                if os.path.isdir(value):
                    self._options[attr] = os.path.abspath(value)

    def __str__(self):
        return str(self._options)

    def __getitem__(self, key):
        return self._options[key]

    def items(self):
        """Simplistic way to do dictionary emulation."""
        return self._options.items()

    def getopt(self, option_name, default=None):
        """Return the option, use None as default."""
        return self._options.get(option_name, default)

    def pp(self):
        print "OPTIONS:"
        for option in sorted(self._options.keys()):
            print "   %-12s  -->  %s" % (option, self._options[option])


class TarsqiError(Exception):
    """Tarsqi Exception class, so far only used in this file."""
    # TODO: should probably be defined elsewhere (in utilities)
    pass


def _read_arguments(args, check=True):
    """ Read the list of arguments given to the tarsqi.py script.  Return a
    tuple with three elements: processing options dictionary, input path and
    output path."""
    options = ['source=', 'pipeline=', 'trap-errors=',
               'perl=', 'loglevel=', 'treetagger=',
               'mallet=', 'classifier=', 'ee-model=', 'et-model=']
    try:
        (opts, args) = getopt.getopt(args, '', options)
        if check and len(args) < 2:
            raise TarsqiError("missing input or output arguments\n%s"
                              % _usage_string())
        return (opts, args)
    except getopt.GetoptError:
        print "ERROR: %s" % sys.exc_value
        sys.exit(_usage_string())


def _usage_string():
    return "Usage: % python tarsqi.py [OPTIONS] INPUT OUTPUT\n" + \
           "See tarsqy.py and docs/manual for more details"


def _log_error(name):
    logger.error("%s error:\n\t%s\n\t%s\n" % (name, sys.exc_type, sys.exc_value))


def _basename(path):
    basename = os.path.basename(path)
    if basename.endswith('.xml'):
        basename = basename[0:-4]
    return basename


def _set_working_directory():
    """Make sure we're in the right directory. If the toolkit crashed on a
    previous file we may be in a different directory. This may also be important
    for those cases where the initially invoced script is not in the TTK_ROOT
    directory, for example when you run the tests."""
    os.chdir(TTK_ROOT)


def run_tarsqi(args):
    """Main method that is called when the script is executed from the command
    line. It creates a Tarsqi instance and lets it process the input. If the
    input is a directory, this method will iterate over the contents, setting up
    Tarsqi instances for all files in the directory. The arguments are the list
    of arguments given by the user on the command line."""
    (opts, args) = _read_arguments(args)
    # Using absolute paths here because some components change the working
    # directory and when some component fails the cwd command may not reset to
    # the root directory
    inpath = os.path.abspath(args[0])
    outpath = os.path.abspath(args[1])
    t0 = time.time()
    if os.path.isdir(inpath):
        if os.path.exists(outpath) and not os.path.isdir(outpath):
            raise TarsqiError(outpath + ' already exists and it is not a directory')
        if not os.path.isdir(outpath):
            os.makedirs(outpath)
        else:
            print "WARNING: Directory %s already exists" % outpath
            print "WARNING: Existing files in %s will be overwritten" % outpath
            print "Continue? (y/n)\n?",
            answer = raw_input()
            if answer != 'y':
                exit()
        for file in os.listdir(inpath):
            infile = inpath + os.sep + file
            outfile = outpath + os.sep + file
            if (os.path.isfile(infile)
                and os.path.basename(infile)[0] != '.'
                and os.path.basename(infile)[-1] != '~'):
                print infile
                Tarsqi(opts, infile, outfile).process_document()
    elif os.path.isfile(inpath):
        if os.path.exists(outpath):
            raise TarsqiError('output file ' + outpath + ' already exists')
        Tarsqi(opts, inpath, outpath).process_document()
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
                                    "--trap-errors=%s" % trap_errors],
                                   check=False)
    tarsqi = Tarsqi(opts, None, None)
    return tarsqi.process_string("<TEXT>%s</TEXT>" % text)


def load_ttk_document(fname, loglevel=2, trap_errors=False):
    """Load a TTK document with all its Tarsqi tags and return the Tarsqi instance
    and the TarsqiDocument instance. Do not run the pipeline, but run the source
    parser, metadata parser and the document structure parser. Used by the
    evaluation code."""
    # For now, we are skipping the link merger because it is too slow on some of
    # the timebank documents
    pipeline = "PREPROCESSOR,GUTIME,EVITA,SLINKET,S2T,BLINKER,CLASSIFIER"
    opts = [('--source', 'ttk'), ('--pipeline', pipeline),
            ('--loglevel',  str(loglevel)), ('--trap-errors', str(trap_errors))]
    tarsqi = Tarsqi(opts, fname, None)
    tarsqi.source_parser.parse_file(tarsqi.input, tarsqi.tarsqidoc)
    tarsqi.metadata_parser.parse(tarsqi.tarsqidoc)
    tarsqi.docstructure_parser.parse(tarsqi.tarsqidoc)
    return (tarsqi, tarsqi.tarsqidoc)



if __name__ == '__main__':
    try:
        if USE_PROFILER:
            run_profiler(sys.argv[1:])
        else:
            run_tarsqi(sys.argv[1:])
    except TarsqiError:
        sys.exit('ERROR: ' + str(sys.exc_value))

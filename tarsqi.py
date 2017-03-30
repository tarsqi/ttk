"""tarsqi.py

Main script that drives all tarsqi toolkit processing.

Source-specific processing is delegated to the docmodel package, which has
access to source parsers and metadata parsers. This script also calls on
various tarsqi modules to do the rest of the real work.


USAGE

   % python tarsqy.py [OPTIONS] [INPUT OUTPUT]

   INPUT/OUTPUT

      Input and output files or directories. If the input is a directory then
      the output directory needs to exist. If one of the options -s --pipe then
      input and output are not required and are ignored if they are there.

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

      --pipe True|False
          With this option set to True the script reads input from the standard
          input and writes output to standard output. The default is False.

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

      --import-event-tags TAGNAME
          With this option the Evita component will try to import existing
          events by lifting tags with name TAGNAME from the source tags.

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
        if isinstance(opts, Options):
            self.options = opts
        else:
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
        logger.info(input_string[:75].replace('\n', ' '))
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


class Options(object):

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
        self.pipe = self.getopt('pipe', False)
        self.loglevel = self.getopt('loglevel')
        self.trap_errors = self.getopt('trap-errors', True)
        self.import_event_tags = self.getopt('import-event-tags')
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
            print "   %-18s  -->  %s" % (option, self._options[option])


class TarsqiError(Exception):
    """Tarsqi Exception class, so far only used in this file."""
    # TODO: should probably be defined elsewhere (in utilities)
    pass


def _read_arguments(args):
    """Read the list of arguments given to the tarsqi.py script.  Return a tuple
    with two elements: processing options dictionary, and remaining arguments
    (input path and output path)."""
    options = ['source=', 'pipeline=', 'trap-errors=', 'loglevel=',
               'pipe=', 'perl=', 'treetagger=', 'import-event-tags=',
               'mallet=', 'classifier=', 'ee-model=', 'et-model=']
    try:
        (opts, args) = getopt.getopt(args, '', options)
        return (opts, args)
    except getopt.GetoptError:
        sys.stderr.write("ERROR: %s\n" % sys.exc_value)
        sys.exit(_usage_string())


def _usage_string():
    return "Usage:\n" + \
        "   % python tarsqi.py [OPTIONS] --pipe\n" + \
        "   % python tarsqi.py [OPTIONS] INPUT OUTPUT\n" + \
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


class TarsqiWrapper(object):

    """Class that wraps the Tarsqi class, taking care of some of the IO aspects."""

    def __init__(self, args):
        (opts, args) = _read_arguments(args)
        self.options = Options(opts)
        self.args = args
        # Set the input path and the output path, these are both set to None
        # when input and output are piped."""
        if self.options.pipe:
            self.inpath = None
            self.outpath = None
        elif len(args) >= 2:
            # Using absolute paths here because some components change the working
            # directory and when some component fails the cwd command may not reset
            # to the root directory
            self.inpath = os.path.abspath(args[0])
            self.outpath = os.path.abspath(args[1])
        else:
            raise TarsqiError("missing --pipe option or missing " +
                              "input or output arguments\n%s" % _usage_string())

    def pp(self):
        print "\n<TarsqiWrapper>"
        print "   inpath  =", self.inpath
        print "   outpath =", self.outpath, "\n"
        self.options.pp()

    def run(self):
        """Main method that is called when the script is executed from the command
        line. It creates a Tarsqi instance and lets it process the input. If the
        input is a directory, this method will iterate over the contents, setting up
        Tarsqi instances for all files in the directory. The arguments are the list
        of arguments given by the user on the command line."""
        t0 = time.time()
        if self.inpath is None and self.outpath is None:
            self._run_tarsqi_on_pipe()
        elif os.path.isdir(self.inpath):
            self._run_tarsqi_on_directory()
        elif os.path.isfile(self.inpath):
            self._run_tarsqi_on_file()
        else:
            raise TarsqiError('Invalid input')
        logger.info("TOTAL PROCESSING TIME: %.3f seconds" % (time.time() - t0))

    def _run_tarsqi_on_pipe(self):
        """Read text from standard input and run tarsqi over it, then print the result
        to standard out."""
        text = sys.stdin.read()
        tarsqi = Tarsqi(self.options, None, None)
        tarsqidoc = tarsqi.process_string(text)
        tarsqidoc.print_all()

    def _run_tarsqi_on_directory(self):
        """Run Tarsqi on all files in a directory."""
        if os.path.exists(self.outpath) and not os.path.isdir(self.outpath):
            raise TarsqiError(self.outpath + ' already exists and it is not a directory')
        if not os.path.isdir(self.outpath):
            os.makedirs(self.outpath)
        else:
            print "WARNING: Directory %s already exists" % outpath
            print "WARNING: Existing files in %s will be overwritten" % outpath
            print "Continue? (y/n)\n?",
            answer = raw_input()
            if answer != 'y':
                exit()
        for file in os.listdir(self.inpath):
            infile = self.inpath + os.sep + file
            outfile = self.outpath + os.sep + file
            if (os.path.isfile(infile)
                and os.path.basename(infile)[0] != '.'
                and os.path.basename(infile)[-1] != '~'):
                print infile
                Tarsqi(self.options, infile, outfile).process_document()

    def _run_tarsqi_on_file(self):
        if os.path.exists(self.outpath):
            raise TarsqiError("output file %s already exists" & self.outpath)
        Tarsqi(self.options, self.inpath, self.outpath).process_document()


def run_profiler(args):
    """Wrap running Tarsqi in the profiler."""
    import profile
    command = "TarsqiWrapper([%s]).run()" % ','.join(['"'+x+'"' for x in args])
    print 'Running profiler on:', command
    profile.run(command, os.path.abspath(PROFILER_OUTPUT))


def process_string(text, pipeline='PREPROCESSOR', loglevel=2, trap_errors=False):
    """Run tarsqi on a bare string without any XML tags, handing in pipeline,
    loglevel and error trapping options."""
    (opts, args) = _read_arguments(["--pipeline=%s" % pipeline,
                                    "--loglevel=%s" % loglevel,
                                    "--trap-errors=%s" % trap_errors])
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
            TarsqiWrapper(sys.argv[1:]).run()
    except TarsqiError:
        sys.exit('ERROR: ' + str(sys.exc_value))

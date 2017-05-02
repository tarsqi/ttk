"""Interface module to Mallet.

Defines a couple of methods that create Mallet commands and a class that
provides an alternative interface.

cvs2vectors_command() creates a command that lets you take a file with lines
like below and create a binary vector file.

    ABC19980108.1830.0711.tml-ei377-ei378 BEFORE e1-asp=NONE e1-cls=OCCURRENCE
    e1-epos=None e1-mod=NONE e1-pol=POS e1-stem=None e1-str=assistance
    e1-tag=EVENT e1-ten=NONE e2-asp=PROGRESSIVE e2-cls=OCCURRENCE e2-epos=None
    e2-mod=NONE e2-pol=NEG e2-stem=None e2-str=helping e2-tag=EVENT
    e2-ten=PRESENT shAsp=1 shTen=1

train_model_command() creates a command that lets you take the binary vector and
create a classifier model.

See the docstring at the bottom of this module for some bitchy notes on
classify_command().

"""

import os, sys
from subprocess import Popen, PIPE

import logger

DEBUG = False

mallet_script = 'mallet.bat' if sys.platform == 'win32' else 'mallet'


def cvs2vectors_command(mallet, vectors, output=False):
    """The command for creating a binary vector file from a text vector
    file. Each line in vectors looks like "ID LABEL FEAT1 FEAT2..."."""
    # I am not sure what token-regex does since I thought it was only important
    # for creating vectors staright from files or directories, but without it
    # accuracy is much lower (early May 2016, with a rather scrappy feature set,
    # we got 0.4 accuracy with it and 0.3 without)
    cvs2vectors_script = os.path.join(mallet, 'bin', 'csv2vectors')
    token_regex = "'[^ ]+'"
    out = "--print-output TRUE > %s.out" % vectors if output else ''
    command = "sh %s --token-regex %s --input %s --output %s.vect" \
              % (cvs2vectors_script, token_regex, vectors, vectors)
    if output:
        command += " --print-output TRUE > %s.out" % vectors
    return command


def train_model_command(mallet, vectors, trainer='MaxEnt',
                        cross_validation=False):
    """The command for creating a model from a binary vector. There is no cross
    validation by default, use cross_validation=5 to turn it on using 5-fold
    cross validation."""
    vects_in = "--input %s.vect" % vectors
    train = "--trainer %s" % trainer
    # with the following we can compare trainers
    # train += " --trainer %s" % 'NaiveBayes'
    model = "--output-classifier %s.model" % vectors
    crossval = ''
    if cross_validation:
        crossval = " --cross-validation %s" % cross_validation
    # report = "--report test:accuracy test:confusion train:raw"
    # report = "--report test:f1:AFTER test:confusion"
    report = "--report test:accuracy test:confusion"
    stdout = "%s.out" % vectors
    stderr = "%s.err" % vectors
    command = "sh %s train-classifier %s %s %s%s %s > %s 2> %s" \
              % (os.path.join(mallet, 'bin', mallet_script),
                 vects_in, train, model, crossval, report, stdout, stderr)
    return command


def classify_command(mallet, vectors, model):
    """The command for running the classifier over a vector file."""
    # NOTE: this command will be removed when MalletClassifier is done
    # TODO: it is not clear whether the --line-regexp, --name and --data options
    # are needed, in fact, limited testing shows they are not; test this a bit
    # more and then delete these options.
    regexp = "--line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\""
    regexp = "--line-regex \"^(\S*)[\s]*(\S*)[\s]*(.*)$\""
    name_and_data = "--name 1 --data 3"
    vectors_in = '--input "%s"' % vectors
    classifier = '--classifier "%s"' % model
    output = '--output -'
    stdout = '"%s.out"' % vectors
    stderr = '"%s.err"' % vectors
    scriptname = os.path.join(mallet, 'bin', mallet_script)
    if not os.path.isfile(scriptname):
        logger.error("Cannot find %s" % scriptname)
    command = "sh %s classify-file %s %s %s %s %s > %s 2> %s" \
              % (scriptname, regexp, name_and_data, vectors_in, classifier, output,
                 stdout, stderr)
    command = command[3:] if sys.platform == 'win32' else command
    return command


def parse_classifier_line(line):
    """Return a pair of the identifier (instance name in Mallet talk) and a
    sorted list of labels and their scores in {score, label) format, with the
    highest score first."""
    fields = line.strip().split()
    identifier = fields.pop(0)
    scores = []
    while fields:
        rel = fields.pop(0)
        score = float(fields.pop(0))
        scores.append((score, rel))
    scores = reversed(sorted(scores))
    return (identifier, list(scores))


class MalletClassifier(object):

    """Currently we take the command and then run a simple os.system(). It
    doesn't really matter for model building, but for classification we should
    at some point use subprocess to do this so we can write to and read from an
    open pipe. This class has the code to do that, but it is not used yet."""

    def __init__(self, mallet, name='--name 1', data='--data 3',
                 regexp="--line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\""):
        """Initialize a classifier by setting its options. All options are
        optional except for mallet which is the directory where Mallet lives."""
        self.mallet = os.path.join(mallet, 'bin', mallet_script)
        # the following are not used when the command is assembled, but some
        # testing is required to see if they are needed after all, my hunch is
        # that they aren't (see below)
        self.name = name
        self.data = data
        self.regexp = regexp
        # a dictionary of classifier models
        self.classifiers = {}

    def __str__(self):
        return "<MalletClassifier %s>" % self.mallet

    def pp(self):
        """Pretty priniter for the MalletClassifier."""
        print "<MalletClassifier>"
        print "   directory  -  %s" % self.mallet
        for classifier in self.classifiers.keys():
            print "   model      -  %s" % classifier

    def add_classifiers(self, *classifier_paths):
        for path in classifier_paths:
            self.classifiers[path] = self._make_pipe(path)
            # this was needed when we fed in the lines one by one, keeping it
            # for future reference
            # self.classifiers[path].stdin.write("\n")

    def classify_file(self):
        """Classify a file and write results to a file. This assumes that input
        vectors are given as a filename and that output goes to a file (that is,
        both vectors and output are not None). This would run a command where
        the command would be very similar to what classify_command() does."""
        # TODO: finish this so it can replace classify_command
        pass

    def classify_vectors(self, classifier, vector_list):
        """Given a list of vectors in string format, run them all through the
        classifier and return the results."""
        vectors = "\n".join(vector_list) + "\n"
        (out, err) = self.classifiers[classifier].communicate(vectors)
        _debug_vectors(vectors, out, err)
        classifier_results = out.rstrip().split("\n")
        # At some point Mallet returned one more line than what went in, having
        # a first garbage line starting with a tab. Remove it. For some reason
        # this does not happen anymore, but I do not know why, so I leave this
        # test here.
        if classifier_results[0].startswith("\t"):
            logger.warn("Unwellformed classifier output:\n%s"
                        % classifier_results[0])
            classifier_results.pop(0)
        return classifier_results

    def _make_pipe(self, classifier):
        """Open a pipe into the classifier command."""
        close_fds = False if sys.platform == 'win32' else True
        command = self._pipe_command(classifier)
        logger.debug("Added pipe on:\n" + command)
        return Popen(command, shell=True, close_fds=close_fds,
                     stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def _pipe_command(self, classifier):
        """Assemble the classifier command for use in a pipe."""
        # TODO: when testing this make sure you allow spaces in the classifier path
        return "sh %s classify-file --input - --output - --classifier %s" \
            % (self.mallet, classifier)

    def _shell_command(self, classifier, vectors):
        """Assemble the classifier command for command line use with input and
        output files."""
        return "sh %s classify-file -- %s %s --output - > %s 2> %s" \
              % (self.mallet,
                 "--input %s" % vectors,
                 "--classifier %s" % classifier,
                 "%s.out" % vectors,
                 "%s.err" % vectors)


def _debug_vectors(vectors, out, err):
    if DEBUG:
        print '>>>', vectors
        print '   [OUT]', out
        print '   [ERR]', err


"""Some notes on classify_command()

Here is what line-regex and friends do (from sh csv2vectors --help):

--line-regex REGEX
  Regular expression containing regex-groups for label, name and data.
  Default is ^(\S*)[\s,]*(\S*)[\s,]*(.*)$

--name INTEGER
  The index of the group containing the instance name. Use 0 to indicate that
   the name field is not used. Default is 1

--label INTEGER
  The index of the group containing the label string. Use 0 to indicate that the
  label field is not used. Default is 2

--data INTEGER
  The index of the group containing the data. Default is 3

So we use the defaults for --name and --data and we can get rid of them. But
--line-regex is slightly different from the default in that the separator for
the 2nd and 3rd group does not have a comma in our case, just the space,
probably so that we can use commas in features. I experimented a bit with
--line-regex, for example trying:

--line-regex "^(\S+) (\S+) (.*)$"

This one fails for reasons I do not understand. I also wondered why this would
not be used on the model training side as well.

It does look like --line-regex can be removed.

"""

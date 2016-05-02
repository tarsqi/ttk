"""Interface module to Mallet.

Defines a couple of methods that create Mallet commands and a class that
provides an alternative interface.

"""

import os
from subprocess import Popen, PIPE


def cvs2vectors_command(mallet, vectors, output=False):
    """The command for creating a binary vector."""
    token_regexp = "--token-regex '[^ ]+'"
    vects_in = "--input %s" % vectors
    vects_out = "--output %s.vect" % vectors
    out = "--print-output TRUE > %s.out" % vectors if output else ''
    command = "sh %s %s %s %s %s" \
              % (os.path.join(mallet, 'bin', 'csv2vectors'),
                 token_regexp, vects_in, vects_out, out)
    return command


def train_model_command(mallet, vectors, trainer='MaxEnt',
                        cross_validation=False):
    """The command for creating a model from a binary vector."""
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
              % (os.path.join(mallet, 'bin', 'mallet'),
                 vects_in, train, model, crossval, report, stdout, stderr)
    return command


def classify_command(mallet, vectors, model):
    """The command for running the classifier over a vector file."""
    # TODO: it is not clear whether the --line-regexp, --name and --data options
    # are needed, in fact, limited testing showed they are not; test this a
    # little bit more and then delete these options.
    regexp = "--line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\""
    name_and_data = "--name 1 --data 3"
    vectors_in = "--input %s" % vectors
    classifier = "--classifier %s" % model
    output = '--output -'
    stdout = "%s.out" % vectors
    stderr = "%s.err" % vectors
    command = "sh %s classify-file %s %s %s %s %s > %s 2> %s" \
              % (os.path.join(mallet, 'bin', 'mallet'), regexp, name_and_data,
                 vectors_in, classifier, output, stdout, stderr)
    return command


class MalletClassifier(object):

    """Currently we take the command and then run a simple os.system(). It
    doesn't really matter for model building, but for classification we should
    at some point use subprocess to do this so we can write to and read from an
    open pipe. This class has the code to do that, but it is not used yet. """

    def __init__(self, mallet, name='--name 1', data='--data 3',
                 regexp="--line-regex \"^(\S*)[\s,]*(\S*)[\s]*(.*)$\""):
        """Initialize a classifier by setting its options. All options are
        optional except for mallet which is the directory where Mallet lives."""
        self.mallet = os.path.join(mallet, 'bin', 'mallet')
        # the following are not used when the command is assembled, but some
        # testing is required to see if they are needed after all
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

    def add_classifier(self, classifier_path):
        self.classifiers[classifier_path] = self._make_pipe(classifier_path)
        self.classifiers[classifier_path].stdin.write("\n")

    def classify_file(self):
        """Classify a file and write results to a file. This assumes that input
        vectors are given as a filename and that output goes to a file (that is,
        both vectors and output are not None). This would run a command where
        the command would be very similar to what classify_command() does."""
        pass

    def classify_line(self, classifier, line):
        self.classifiers[classifier].stdin.write(line)
        result = self.classifiers[classifier].stdout.readline()
        return result

    def _make_pipe(self, classifier):
        """Open a pipe into the classifier command."""
        return Popen(self._command(classifier), shell=True, close_fds=True,
                     stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def _command(self, classifier):
        """Assemble the classifier command."""
        return "sh %s classify-file --input - --output - --classifier %s" \
            % (self.mallet, classifier)

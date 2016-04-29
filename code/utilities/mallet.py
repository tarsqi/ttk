"""

Module to provide an interface to Mallet.

Defines a couple of methods that create Mallet commands.

"""

import os

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
    stdout = "%s.stdout.txt" % vectors
    stderr = "%s.stderr.txt" % vectors
    command = "sh %s train-classifier %s %s %s%s %s > %s 2> %s" \
              % (os.path.join(mallet, 'bin', 'mallet'),
                 vects_in, train, model, crossval, report, stdout, stderr)
    return command


def classify_command(mallet, vectors, model):
    """The command for running the classifier over a vector file."""
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


# TODO. Currently we take the command and then run a simple os.system. It
# doesn't really matter for model building, but for classification we should at
# some point use subprocess to do this so we can write to and read from an open
# pipe. There should be some code to support that in this script.

# Here are some snippets:
#
# def GetNer(ner_model):
#   command = 'java -Xmx256m -cp %s/mallet-2.0.6/lib/mallet-deps.jar:%s/mallet-2.0.6/class
#       cc.mallet.fst.SimpleTaggerStdin --weights sparse --model-file %s/models/ner/%s'
#       % (BASE_DIR, BASE_DIR, BASE_DIR, ner_model)
#   return subprocess.Popen(command, shell=True, close_fds=True,
#       stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#
# ner.stdin.write(("\t".join(seq_features) + "\n").encode('utf8'))
# ner.stdout.readline().rstrip('\n').strip(' ')

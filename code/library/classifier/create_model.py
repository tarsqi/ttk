"""Create a MaxEnt model.

Usage:

$ python create_model.py <VECTORS_FILE>

The vectors file is the text file created by create_vectors.py. By default, this
will use the MaxEnt classifier and perfrom no cross validation. Edit the TRAINER
and CROSS_VALIDATION variables to change this behaviour.

The command above creates the following files:

   <VECTORS_FILE>.model
   <VECTORS_FILE>.stderr.out
   <VECTORS_FILE>.stdout.txt
   <VECTORS_FILE>.vect

The first one is the one needed for running the classifier.

"""


import os, sys, glob


# User settings ---------------------------------------------------------------

# Directory with the Mallet code, containing the 'bin' sub directory
MALLET_DIR = '/Applications/ADDED/nlp/mallet/mallet-2.0.7'

# The default algorithm used
TRAINER = 'MaxEnt'

# Set to True to perform 10-fold cross validation
CROSS_VALIDATION = False

# -----------------------------------------------------------------------------



MALLET = os.path.join(MALLET_DIR, 'bin', 'mallet')
CVS2VECTORS = os.path.join(MALLET_DIR, 'bin', 'csv2vectors')


def create_model(vectors, trainer='MaxEnt',
                 cross_validation=None, output=False):
    remove_files(vectors)
    commands = [cvs2vectors_command(vectors, output=output),
                train_model_command(vectors, trainer=trainer,
                                    cross_validation=cross_validation)]
    for command in commands:
        run_command(command)


def remove_files(vectors):
    for fname in glob.glob("%s.*" % vectors):
        os.remove(fname)


def cvs2vectors_command(vectors, output=False):
    token_regexp = "--token-regex '[^ ]+'"
    vects_in = "--input %s" % vectors
    vects_out = "--output %s.vect" % vectors
    out = "--print-output TRUE > %s.out" % vectors if output else ''
    command = "sh %s %s %s %s %s" % (CVS2VECTORS, token_regexp, vects_in, vects_out, out)
    return command


def train_model_command(vectors, trainer='MaxEnt', cross_validation=False):
    vects_in = "--input %s.vect" % vectors
    train = "--trainer %s" % trainer
    # train += " --trainer %s" % 'NaiveBayes'
    model = "--output-classifier %s.model" % vectors
    crossval = ''
    if cross_validation:
        crossval = " --training-portion 0.9 --num-trials 10"
    report = "--report test:accuracy test:confusion train:raw"
    report = "--report test:accuracy test:confusion"
    stdout = "%s.stdout.txt" % vectors
    stderr = "%s.stderr.txt" % vectors
    command = "sh %s train-classifier %s %s %s%s %s > %s 2> %s" \
              % (MALLET, vects_in, train, model, crossval, report, stdout, stderr)
    return command

    
def run_command(command):
    print command
    os.system(command)
    

if __name__ == '__main__':
    
    vectors_file = sys.argv[1]
    create_model(vectors_file, trainer=TRAINER, cross_validation=CROSS_VALIDATION)

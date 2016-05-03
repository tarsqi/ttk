"""Create a MaxEnt model.

Usage:

$ python create_model.py OPTIONS <VECTORS_FILE>

Options:

   --mallet-dir DIR

      Directory where Mallet lives, it should contain the bin subdirectory. The
      default is set by the MALLET variable below.

   --cross-validation N

      There is no cross validation by default, set this to a number to turn
      validation on, for example, with 5 you will get 5-fold cross validation.

   --trainer 'MaxEnt'|'NaiveBayes'|'C45'|'DecisionTree'|...

      One of the trainers allowed by Mallet, the Mallet API at
      http://mallet.cs.umass.edu/api/ has a list somewhere in the
      cs.mallet.classify package. The default is MaxEnt.

The vectors file is the text file created by create_vectors.py. By default, this
will use the MaxEnt classifier and perform no cross validation. Edit the TRAINER
and CROSS_VALIDATION variables to change this behaviour.

The script creates the following files:

   <VECTORS_FILE>.model
   <VECTORS_FILE>.err
   <VECTORS_FILE>.out
   <VECTORS_FILE>.vect

The first one is the one needed for running the classifier. Note that if cross
validation is on then there will be no .model file, instead there will be models
for each fold.

"""


import os, sys, glob, getopt
import path
from utilities import mallet


# Default settings

# Directory with the Mallet code, containing the 'bin' sub directory
MALLET = '/Applications/ADDED/nlp/mallet/mallet-2.0.7'

# The default algorithm used
TRAINER = 'MaxEnt'

# Set to a number n to perform n-fold cross validation
CROSS_VALIDATION = False


def create_model(vectors, trainer='MaxEnt',
                 cross_validation=None, output=False):
    """Create a Mallet model given a vectors file."""
    remove_files(vectors)
    commands = [mallet.cvs2vectors_command(MALLET, vectors, output=output),
                mallet.train_model_command(MALLET, vectors, trainer=trainer,
                                           cross_validation=cross_validation)]
    for command in commands:
        print command
        os.system(command)


def remove_files(vectors):
    """Remove all files derived from the vectors file."""
    for fname in glob.glob("%s.*" % vectors):
        os.remove(fname)
    

if __name__ == '__main__':

    options = ["mallet-dir=", "cross-validation=", "trainer="]
    opts, args = getopt.getopt(sys.argv[1:], '', options)
    for opt, val in opts:
        if opt == '--mallet-dir':
            MALLET = val
        if opt == '--trainer':
            TRAINER = val
        if opt == '--cross-validation':
            CROSS_VALIDATION = int(val)
    vectors_file = args[0]
    create_model(vectors_file, trainer=TRAINER, cross_validation=CROSS_VALIDATION)

"""compile_patterns.py

Take all the Evita multi-chunk patterns, compile them into FSAs, and save them
in pickle files in this directory.

The following files are created:

   BECOME_A_FSAs.pickle
   BE_A_FSAs.pickle
   BE_FSAs.pickle
   BE_N_FSAs.pickle
   CONTINUE_A_FSAs.pickle
   DO_FSAs.pickle
   GOINGto_FSAs.pickle
   HAVE_FSAs.pickle
   KEEP_A_FSAs.pickle
   MODAL_FSAs.pickle
   USEDto_FSAs.pickle

After creation these should be moved to the patterns directory.

"""

import os, sys, cPickle

sys.path.append('../..')

# This is ugly, but we need to do this because multi_chunk_patterns imports
# library.forms which needs the TTK_ROOT environment variable; however, the
# variable is not used so we hand in a dummy value
os.environ['TTK_ROOT'] = 'DUMMY'

# TODO: why not just import root???


from utilities.FSA import compileOP
from library.evita.multi_chunk_patterns import patternsGroups

for (listName, patternsList) in patternsGroups:
    fname = "%s.pickle" % listName
    pickleFile = open(fname, 'w')
    print "Compiling %d %s and saving them in %s" % (len(patternsList), listName, fname)
    toPickle = []
    for name, pattern in patternsList:
        toPickle.append(compileOP(pattern, name=name))
    cPickle.dump(toPickle, pickleFile)

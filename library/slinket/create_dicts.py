"""create_dicts.py

Takes dictionaries in slinkPredicates and alinkPredicates and the asscoiated
compiled patterns in slinketPatterns and converts them into pickle objects that
are saved in the current directory.

The pickle files should be moved to the dictionaries directory.

TODO:

The code in slinkPredicates.py and alinkPredicates.py depended on the old way of
importing TimeML specifications and was not updated to usie the TarsqiLibrary in
library.main. For now I used the hack of adding an old timeMLspec.py file to
this directory and use that instead.

"""




from __future__ import absolute_import
from __future__ import print_function
import os, sys, six.moves.cPickle
from io import open

sys.path.append('../..')

# This is ugly, but we need to do this because slinketPatterns imports
# library.forms which needs the TTK_ROOT environment variable; however, the
# variable is not used so we hand in a dummy value
os.environ['TTK_ROOT'] = 'DUMMY'

from . import slinkPredicates
from . import alinkPredicates


print("Pickling dictionaries...")
slink_dictionaries = [(slinkPredicates.nounDict, "slinkNouns"),
                      (slinkPredicates.adjDict, "slinkAdjs"),
                      (slinkPredicates.verbDict, "slinkVerbs"),
                      (alinkPredicates.nounDict, "alinkNouns"),
                      (alinkPredicates.verbDict, "alinkVerbs")]

for (dictionary, name) in slink_dictionaries:
    fname = "%s.pickle" % name
    pickleFile = open(fname, 'w')
    print("Writing %s to %s" % (name, fname))
    six.moves.cPickle.dump(dictionary, pickleFile)

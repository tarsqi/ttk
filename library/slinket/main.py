from __future__ import absolute_import
import os
import six.moves.cPickle
from io import open

TTK_ROOT = os.environ['TTK_ROOT']
DIR_DICTS = os.path.join(TTK_ROOT, 'library', 'slinket', 'dictionaries')


class SlinketDicts(object):

    def __init__(self):
        self.slinkVerbsDict = None
        self.slinkNounsDict = None
        self.slinkAdjsDict = None
        self.alinkVerbsDict = None
        self.alinkNounsDict = None

    def load(self):
        """Load the Slinket dictionaries if they have not been loaded yet."""
        if not self.slinkVerbsDict:
            self.slinkVerbsDict = six.moves.cPickle.load(open(os.path.join(DIR_DICTS, "slinkVerbs.pickle"), 'rb'))
            self.slinkNounsDict = six.moves.cPickle.load(open(os.path.join(DIR_DICTS, "slinkNouns.pickle"), 'rb'))
            self.slinkAdjsDict = six.moves.cPickle.load(open(os.path.join(DIR_DICTS, "slinkAdjs.pickle"), 'rb'))
            self.alinkVerbsDict = six.moves.cPickle.load(open(os.path.join(DIR_DICTS, "alinkVerbs.pickle"), 'rb'))
            self.alinkNounsDict = six.moves.cPickle.load(open(os.path.join(DIR_DICTS, "alinkNouns.pickle"), 'rb'))

SLINKET_DICTS = SlinketDicts()

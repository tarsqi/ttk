"""stemmer.py

Contains an utterly simplistic stemmer.

Originally we used a stripped down version of the Porter stemmer, but the
version in here performed at the same level. Note that this stemmer is only used
for those cases when a token does not have a lemma.

"""

from library.forms import STEM_EXCEPTIONS_FILE
from binsearch import binarySearchFile


class Stemmer:

    def __init__(self):
        self.exceptionsFile = open(STEM_EXCEPTIONS_FILE, 'r')

    def stem(self, key):
        """Look up key in stem exceptions file. Use the porter stemmer
        if key is not in exceptions file. """
        line = binarySearchFile(self.exceptionsFile, key)
        if line:
            (form, stem) = line.split()
            return stem
        else:
            return strip_plural(key)


def strip_plural(token):
    """Strip away what looks like a plural s."""
    if token.endswith('esses'):
        return token[:-2]
    elif token.endswith('s') and not token.endswith('ss'):
        # dogs->dogs, but not loss->los
        return token[:-1]
    return token

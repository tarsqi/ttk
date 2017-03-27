import os
import cPickle

TTK_ROOT = os.environ['TTK_ROOT']
DIR_PATTERNS = os.path.join(TTK_ROOT, 'library', 'evita', 'patterns')


def openfile(basename):
    return open(os.path.join(DIR_PATTERNS, basename))


# EVITA PATTERNS

HAVE_FSAs = cPickle.load(openfile("HAVE_FSAs.pickle"))
MODAL_FSAs = cPickle.load(openfile("MODAL_FSAs.pickle"))
BE_N_FSAs = cPickle.load(openfile("BE_N_FSAs.pickle"))
BE_A_FSAs = cPickle.load(openfile("BE_A_FSAs.pickle"))
BE_FSAs = cPickle.load(openfile("BE_FSAs.pickle"))
GOINGto_FSAs = cPickle.load(openfile("GOINGto_FSAs.pickle"))
USEDto_FSAs = cPickle.load(openfile("USEDto_FSAs.pickle"))
DO_FSAs = cPickle.load(openfile("DO_FSAs.pickle"))
BECOME_A_FSAs = cPickle.load(openfile("BECOME_A_FSAs.pickle"))
CONTINUE_A_FSAs = cPickle.load(openfile("CONTINUE_A_FSAs.pickle"))
KEEP_A_FSAs = cPickle.load(openfile("KEEP_A_FSAs.pickle"))

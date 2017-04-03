"""

Settings that determine the behaviour of Evita components.

"""

DEBUG = False


# Proper names are allowed to be nominal events, set to False disallow events
# where the head has a NNP or NNPS tag
INCLUDE_PROPERNAMES = True

# Determines whether we try to disambiguate nominals with training data
EVITA_NOM_DISAMB = True

# Determines whether we use context information in training data (has no effect if
# EVITA_NOM_DISAMB is False).
EVITA_NOM_CONTEXT = True

# Determines how we use WordNet to recognize events. If True, mark only forms
# whose first WN sense is an event sense, if False, mark forms which have any
# event sense (if EVITA_NOM_DISAMB is true, this is only a fallback where no
# training data exists).
EVITA_NOM_WNPRIMSENSE_ONLY = True


if DEBUG:
    print "EVITA_NOM_DISAMB = %s" % EVITA_NOM_DISAMB
    print "EVITA_NOM_CONTEXT = %s" % EVITA_NOM_CONTEXT
    print "EVITA_NOM_WNPRIMSENSE_ONLY = %s" % EVITA_NOM_WNPRIMSENSE_ONLY


"""

Contains a Bayesian disambiguator.

"""


DEBUG_BAYES = False

# Specify at which frequency training data are allowed to have an impact on sense
# disambiguation
MINIMAL_FREQUENCY = 2.0


def _debug(string):
    """Debugging method"""
    if DEBUG_BAYES: print string


class DisambiguationError(LookupError):
    """Use a special exception class to distinguish general KeyErrors from
    errors due to failed disambiguation."""
    pass


class BayesEventRecognizer:
    """Simple Bayesian disambiguator. The only features used are the pos
    tag and the definiteness of the noun chunk."""

    def __init__(self, senseProbs, condProbs):
        """Initialize with dictionaries of sense frequencies/probabilities and
        conditional probabilities that take features into account."""
        self.senseProbs = senseProbs
        self.condProbs = condProbs


    def isEvent(self, lemma, features):
        """Return True if lemma is an event, False if it is not, and raise a
        DisambiguationError if there is not enough data for a decision."""

        senseProbData = self.senseProbs.get(lemma, [0.0, 0.0])
        _debug("BayesEventRecognizer.isEvent("+lemma+")")
        _debug("  " + str(senseProbData))

        # calculate probabilities from frequency data, refuse to do anything if
        # frequencies are too low
        frequency = senseProbData[0] + senseProbData[1]
        if frequency < MINIMAL_FREQUENCY:
            raise DisambiguationError('sparse data for "' + lemma + '"')
        probEvent = senseProbData[1] / frequency
        probNonEvent = 1 - probEvent
        _debug("  " + str(probEvent) + " > " + str(probNonEvent))

        # return now if probabilities are absolute
        if probEvent == 1:
            return True
        if probNonEvent == 1:
            return False

        # adjust probablities with probabilities of contextual features, ignore
        # features for which we have no data
        for feature in features:
            try:
                probs = self.condProbs[lemma][feature]
                _debug("  "+feature+": "+str(probs))
                probEvent *= probs[1]
                probNonEvent *= probs[0]
            except KeyError:
                pass

        _debug("  " + str(probEvent) + " > " + str(probNonEvent))
        return probEvent > probNonEvent

"""

Contains a Bayesian disambiguator.

"""

from library import forms
from utilities.file import open_pickle_file
from utilities import logger


# Open pickle files with semcor information
DictSemcorEvent = open_pickle_file(forms.DictSemcorEventPickleFilename)
DictSemcorContext = open_pickle_file(forms.DictSemcorContextPickleFilename)
# TODO: these should not be specified in forms but somewhere in the evita
# library (similar to how Slinket does it)

# Specify at which frequency training data are allowed to have an impact on sense
# disambiguation
MINIMAL_FREQUENCY = 2.0


def get_classifier():
    return BayesEventRecognizer(DictSemcorEvent, DictSemcorContext)


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
        logger.debug("BayesEventRecognizer.isEvent("+lemma+")")
        logger.debug("\traw counts: " + str(senseProbData))

        # calculate probabilities from frequency data, refuse to do anything if
        # frequencies are too low
        frequency = senseProbData[0] + senseProbData[1]
        if frequency < MINIMAL_FREQUENCY:
            raise DisambiguationError('sparse data for "' + lemma + '"')
        probEvent = senseProbData[1] / frequency
        probNonEvent = 1 - probEvent
        logger.debug("\tprobabilities: non-event=%s event=%s" % (probNonEvent, probEvent))

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
                logger.debug("\tfeature prob: %s=%s" % (feature, probs))
                probEvent *= probs[1]
                probNonEvent *= probs[0]
            except KeyError:
                pass

        logger.debug("\tadjusted probabilities: non-event=%s event=%s" % (probNonEvent, probEvent))
        return probEvent > probNonEvent

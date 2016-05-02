"""

Python wrapper around the Mallet Classifier

"""

import os

from library.tarsqi_constants import CLASSIFIER
from library.timeMLspec import TLINK, EIID, TID
from library.timeMLspec import RELTYPE, ORIGIN, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME
from utilities import logger, mallet
from components.classifier import vectors

TTK_ROOT = os.environ['TTK_ROOT']


class ClassifierWrapper:
    """Wraps the maxent link classifier."""

    def __init__(self, document):
        self.component_name = CLASSIFIER
        self.document = document
        self.models = os.path.join(TTK_ROOT,
                                   'components', 'classifier', 'models')
        self.data = os.path.join(TTK_ROOT, 'data', 'tmp')
        options = self.document.options
        self.mallet = options.mallet
        self.classifier = options.classifier
        self.ee_model = os.path.join(self.models, options.ee_model)
        self.et_model = os.path.join(self.models, options.et_model)

    def process(self):
        """Create files with vectors and hand them to the classifier for
        processing. Processing will update the document's tag repository
        when tlinks are added. """
        # self.process_future(); return
        ee_vectors = os.path.join(self.data, "vectors.EE")
        et_vectors = os.path.join(self.data, "vectors.ET")
        ee_results = ee_vectors + '.out'
        et_results = et_vectors + '.out'
        vectors.create_tarsqidoc_vectors(self.document, ee_vectors, et_vectors)
        commands = [
            mallet.classify_command(self.mallet, ee_vectors, self.ee_model),
            mallet.classify_command(self.mallet, et_vectors, self.et_model)]
        for command in commands:
            logger.debug(command)
            os.system(command)
        self._add_links(ee_vectors, et_vectors, ee_results, et_results)

    def process_future(self):
        """This is an alternative way to do process() that is not used yet. The
        difference is that it uses subprocess instead of os.system() and that it
        pipes each line to the classifier, not using any temporary files. It has
        one weird problem, which is that when we process the very first line the
        identifier is missing from the output."""
        (ee_vectors, et_vectors) \
            = vectors.collect_tarsqidoc_vectors(self.document)
        mc = mallet.MalletClassifier(self.mallet)
        mc.add_classifier(self.ee_model)
        mc.add_classifier(self.et_model)
        ee_results = []
        et_results = []
        for v in ee_vectors:
            result = mc.classify_line(self.ee_model, "%s\n" % v)
            ee_results.append(_fix_missing_id(v, result))
        for v in et_vectors:
            result = mc.classify_line(self.et_model, "%s\n" % v)
            et_results.append(_fix_missing_id(v, result))
        self._add_links_future(ee_results, et_results)

    def _add_links(self, ee_vectors, et_vectors, ee_results, et_results):
        """Insert new tlinks into the document using the vectors and the results
        from the classifier."""
        for (f1, f2) in ((ee_vectors, ee_results), (et_vectors, et_results)):
            vector_file = open(f1)
            classifier_file = open(f2)
            for line in vector_file:
                vector_id = self._parse_vector_identifier(line)
                classifier_line = classifier_file.readline()
                result_id, scores = self._parse_classifier_line(classifier_line)
                if vector_id != result_id:
                    print 'WARNING: vector and classification do not match'
                    continue
                id1 = result_id.split('-')[-2]
                id2 = result_id.split('-')[-1]
                attrs = { RELTYPE: scores[0][1],
                          ORIGIN: "%s-%.4f" % (CLASSIFIER, scores[0][0]),
                          _arg1_attr(id1): id1,
                          _arg2_attr(id2): id2 }
                self.document.tags.add_tag(TLINK, -1, -1, attrs)

    def _add_links_future(self, ee_results, et_results):
        """Insert new tlinks into the document using the results from the
        classifier."""
        for classifier_results in (ee_results, et_results):
            for line in classifier_results:
                result_id, scores = self._parse_classifier_line(line)
                id1 = result_id.split('-')[-2]
                id2 = result_id.split('-')[-1]
                attrs = { RELTYPE: scores[0][1],
                          ORIGIN: "%s-%.4f" % (CLASSIFIER, scores[0][0]),
                          _arg1_attr(id1): id1,
                          _arg2_attr(id2): id2 }
                self.document.tags.add_tag(TLINK, -1, -1, attrs)

    def _parse_vector_identifier(self, line):
        """Return the identifier from the vector string. """
        return line.split()[0]

    def _parse_classifier_line(self, line):
        """Extract relType, confidence correct/incorrect and correct relation
        from the classifier result line."""
        fields = line.strip().split()
        identifier = fields.pop(0)
        scores = []
        while fields:
            rel = fields.pop(0)
            score = float(fields.pop(0))
            scores.append((score, rel))
        scores = reversed(sorted(scores))
        return (identifier, list(scores))


def _arg1_attr(identifier):
    """Determine the attribute name for the first argument."""
    return TIME_ID if identifier.startswith('t') \
        else EVENT_INSTANCE_ID


def _arg2_attr(identifier):
    """Determine the attribute name for the second argument."""
    return RELATED_TO_TIME if identifier.startswith('t') \
        else RELATED_TO_EVENT_INSTANCE


def _fix_missing_id(vector, result):
    """This is to fix a weird problem with the MalletClassifier where when
    reading the first line from the output the identifier is missing. Use the
    vector's identifier to add it back on."""
    if result.startswith("\t"):
        return "%s%s" % (vector.identifier, result)
    else:
        return result

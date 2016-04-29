"""

Python wrapper around the Mallet Classifier

"""

import os

from library.tarsqi_constants import CLASSIFIER
from library.timeMLspec import TLINK, EIID, TID
from library.timeMLspec import RELTYPE, ORIGIN, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME
from utilities import mallet
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
        self.mallet = self.document.options.mallet

    def process(self):
        """Create files with vectors and hand them to the classifier for
        processing. Processing will update the document's tag repository
        when tlinks are added. """
        ee_model = os.path.join(self.models, 'tb-vectors.ee.model')
        et_model = os.path.join(self.models, 'tb-vectors.et.model')
        ee_vectors = os.path.join(self.data, "vectors.EE")
        et_vectors = os.path.join(self.data, "vectors.ET")
        ee_results = ee_vectors + '.out'
        et_results = et_vectors + '.out'
        vectors.create_tarsqidoc_vectors(self.document, ee_vectors, et_vectors)
        commands = [mallet.classify_command(self.mallet, ee_vectors, ee_model),
                    mallet.classify_command(self.mallet, et_vectors, et_model)]
        for command in commands:
            print command
            os.system(command)
        self._add_links(ee_vectors, et_vectors, ee_results, et_results)

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

"""

Python wrapper around the Mallet Classifier

"""

import os

from library.tarsqi_constants import CLASSIFIER
from library.main import LIBRARY
from utilities import logger, mallet
from components.classifier import vectors

TTK_ROOT = os.environ['TTK_ROOT']

TLINK = LIBRARY.timeml.TLINK
EIID = LIBRARY.timeml.EIID
TID = LIBRARY.timeml.TID
LID = LIBRARY.timeml.LID
RELTYPE = LIBRARY.timeml.RELTYPE
ORIGIN = LIBRARY.timeml.ORIGIN
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
TIME_ID = LIBRARY.timeml.TIME_ID
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME


class ClassifierWrapper:

    """Wraps the maxent link classifier."""

    def __init__(self, document):
        self.component_name = CLASSIFIER
        self.tarsqidoc = document             # instance of TarsqiDocument
        self.models = os.path.join(TTK_ROOT,
                                   'components', 'classifier', 'models')
        self.data = os.path.join(TTK_ROOT, 'data', 'tmp')
        options = self.tarsqidoc.options
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
        vectors.create_tarsqidoc_vectors(self.tarsqidoc, ee_vectors, et_vectors)
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
        # TODO: when this is tested enough let it replace process()
        (ee_vectors, et_vectors) \
            = vectors.collect_tarsqidoc_vectors(self.tarsqidoc)
        mc = mallet.MalletClassifier(self.mallet)
        mc.add_classifiers(self.ee_model, self.et_model)
        ee_in = [str(v) for v in ee_vectors]
        et_in = [str(v) for v in et_vectors]
        ee_results = mc.classify_vectors(self.ee_model, ee_in)
        et_results = mc.classify_vectors(self.et_model, et_in)
        self._add_links_future(ee_results, et_results)

    def _add_links(self, ee_vectors, et_vectors, ee_results, et_results):
        """Insert new tlinks into the document using the vectors and the results
        from the classifier."""
        for (f1, f2) in ((ee_vectors, ee_results), (et_vectors, et_results)):
            vector_file = open(f1)
            classifier_file = open(f2)
            for line in vector_file:
                vector_id = _get_vector_identifier(line)
                classifier_line = classifier_file.readline()
                result_id, scores = mallet.parse_classifier_line(classifier_line)
                if vector_id != result_id:
                    print 'WARNING: vector and classification do not match'
                    continue
                id1 = result_id.split('-')[-2]
                id2 = result_id.split('-')[-1]
                attrs = { LID: self.tarsqidoc.next_link_id(TLINK),
                          RELTYPE: scores[0][1],
                          ORIGIN: "%s-%.4f" % (CLASSIFIER, scores[0][0]),
                          _arg1_attr(id1): id1,
                          _arg2_attr(id2): id2 }
                self.tarsqidoc.tags.add_tag(TLINK, -1, -1, attrs)

    def _add_links_future(self, ee_results, et_results):
        """Insert new tlinks into the document using the results from the
        classifier."""
        # TODO: when this is tested enough let it replace process()
        for classifier_results in (ee_results, et_results):
            for line in classifier_results:
                result_id, scores = mallet.parse_classifier_line(line)
                id1 = result_id.split('-')[-2]
                id2 = result_id.split('-')[-1]
                reltype = scores[0][1]
                origin = "%s-%.4f" % (CLASSIFIER, scores[0][0])
                attrs = { LID: self.tarsqidoc.next_link_id(TLINK),
                          RELTYPE: reltype, ORIGIN: origin,
                          _arg1_attr(id1): id1, _arg2_attr(id2): id2 }
                print attrs
                self.tarsqidoc.tags.add_tag(TLINK, -1, -1, attrs)


def _get_vector_identifier(line):
    """Return the identifier from the vector string. """
    return line.split()[0]


def _arg1_attr(identifier):
    """Determine the attribute name for the first argument."""
    return TIME_ID if identifier.startswith('t') \
        else EVENT_INSTANCE_ID


def _arg2_attr(identifier):
    """Determine the attribute name for the second argument."""
    return RELATED_TO_TIME if identifier.startswith('t') \
        else RELATED_TO_EVENT_INSTANCE

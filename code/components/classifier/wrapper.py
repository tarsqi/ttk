"""

Python wrapper around the MaxEnt Classifier

CLASSES
   ClassifierWrapper

"""

import os

from library.tarsqi_constants import CLASSIFIER
from library.timeMLspec import TLINK, EIID, TID
from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, ORIGIN, CONFIDENCE
from utilities import logger
from components.classifier import vectors

TTK_ROOT = os.environ['TTK_ROOT']


class ClassifierWrapper:
    """Wraps the maxent link classifier."""

    def __init__(self, document):
        self.component_name = CLASSIFIER
        self.document = document
        self.DIR_CLASSIFIER = os.path.join(TTK_ROOT, 'components', 'classifier')
        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')
        platform = self.document.options.platform
        if platform == 'linux2':
            self.executable = 'mxtest.opt.linux'
        elif platform == 'darwin':
            self.executable = 'mxtest.opt.osx'

    def process(self):
        """Retrieve the elements and hand them to the classifier for
        processing. Processing will update the element's tarsqi_tag
        repository when tlinks are added."""
        os.chdir(self.DIR_CLASSIFIER)
        ee_model = os.path.join('data', 'op.e-e.model')
        et_model = os.path.join('data', 'op.e-t.model')
        ee_vectors = os.path.join(self.DIR_DATA, "vectors.EE")
        et_vectors = os.path.join(self.DIR_DATA, "vectors.ET")
        ee_results = ee_vectors + '.REL'
        et_results = et_vectors + '.REL'
        vectors.create_tarsqidoc_vectors(self.document, ee_vectors, et_vectors)
        commands = [
            "./%s -input %s -model %s -output %s > class.log" %
            (self.executable, ee_vectors, ee_model, ee_results),
            "./%s -input %s -model %s -output %s > class.log" %
            (self.executable, et_vectors, et_model, et_results)]
        exit()
        for command in commands:
            os.system(command)
        self._add_links(ee_vectors, et_vectors,
                        ee_results, et_results)

    def _add_links(self, ee_vectors, et_vectors, ee_results, et_results):
        """Insert new tlinks into the element using the vectors and the results
        from the classifier."""
        for (f1, f2) in ((ee_vectors, ee_results), (et_vectors, et_results)):
            vector_file = open(f1)
            classifier_file = open(f2)
            for line in vector_file:
                classifier_line = classifier_file.readline()
                attrs = self._parse_vector_string(line)
                id1 = self._get_id('0', attrs, line)
                id2 = self._get_id('1', attrs, line)
                (rel, confidence) = self._parse_classifier_line(classifier_line)[0:2]
                origin = CLASSIFIER + '-' + confidence
                id1_attr = TIME_ID if id1.startswith('t') else EVENT_INSTANCE_ID
                id2_attr = RELATED_TO_TIME if id2.startswith('t') else RELATED_TO_EVENT_INSTANCE
                attrs = {RELTYPE: rel,
                         id1_attr: id1,
                         id2_attr: id2,
                         ORIGIN: origin}
                self.document.tags.add_tag(TLINK, -1, -1, attrs)

    def _parse_vector_string(self, line):
        """Return the attribute dictionaries from the vector string. """
        attrs = {}
        for pair in line.split():
            if pair.find('-') > -1:
                (attr, val) = pair.split('-', 1)
                attrs[attr] = val
        return attrs

    def _parse_classifier_line(self, line):
        """Extract relType, confidence correct/incorrect and correct relation
        from the classifier result line."""
        line = line.strip()
        (rel, confidence, judgment, correct_judgement) = line.split()
        return (rel, confidence, judgment, correct_judgement)

    def _get_id(self, prefix, attrs, line):
        """Get the eiid or tid for the first or second object in the
        vector. The prefix is '0' or '1' and determines which object's
        id is returned."""
        id = attrs.get(prefix+EIID, attrs.get(prefix+TID, None))
        if not id:
            logger.warn("Could not find id in " + line)
        return id

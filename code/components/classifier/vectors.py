"""

This module is responsible for creating the vectors in text format that are
input to the mallet trainer and classifier.

If input is created for the classifier then it looks like

   UNKNOWN e-aspect=NONE e-class=OCCURRENCE e-epos=VERB e-modality=NONE
   e-polarity=POS e-stem=None e-string=put e-tag=EVENT e-tense=PASTPART
   t-string=2013 t-tag=TIMEX3 t-type=DATE t-value=2013 order=et signal=before

If input is create for model building then it looks like

   BEFORE e-aspect=NONE e-class=OCCURRENCE e-epos=VERB e-modality=NONE
   e-polarity=POS e-stem=None e-string=put e-tag=EVENT e-tense=PASTPART
   t-string=2013 t-tag=TIMEX3 t-type=DATE t-value=2013 order=et signal=before

"""

import os, textwrap

from components.common_modules.tree import create_tarsqi_tree

from library.timeMLspec import EVENT, EID, EIID, CLASS, STEM, EPOS
from library.timeMLspec import TENSE, ASPECT, MODALITY, POLARITY
from library.timeMLspec import TIMEX, TID, TYPE, VALUE

# Determines what attributes to use for the vector, the TID and EIID attributes
# are used so we can go back from the vector to an actual tlink. It is assumed
# that having these attributes in the vector has o impact on classification
# results. TOOO: if this assumption is wrong then the model building code should
# filter on these attributes.
EVENT_FEATURES = [EIID, CLASS, STEM, EPOS, TENSE, ASPECT, MODALITY, POLARITY]
TIMEX_FEATURES = [TID, TYPE, VALUE]

TAG = 'tag'
FUNINDOC = 'funInDoc'
TEMPFUN = 'tempFun'
STRING = 'string'
SHIFT_TENSE = 'shiftTense'
SHIFT_ASPECT = 'shiftAspect'
ORDER = 'order'
SIGNAL = 'signal'

DEBUG = False
#DEBUG = True


def create_tarsqidoc_vectors(tarsqidoc, ee_file, et_file):
    """Create vectors for the TarsqiDocument and write them to two files."""
    (ee_vectors, et_vectors) = collect_tarsqidoc_vectors(tarsqidoc)
    write_vectors(ee_file, ee_vectors, et_file, et_vectors)


def collect_tarsqidoc_vectors(tarsqidoc):
    """Collect vectors for the TarsqiDocument."""
    ee_vectors = []
    et_vectors = []
    for element in tarsqidoc.elements():
        tree = create_tarsqi_tree(tarsqidoc, element)
        for s in tree:
            _create_vectors_for_sentence(tarsqidoc, element, s,
                                         ee_vectors, et_vectors)
    return (ee_vectors, et_vectors)


def write_vectors(ee_file, ee_vectors, et_file, et_vectors):
    """Write the vectors to files."""
    ee_fh = open(ee_file, 'w')
    et_fh = open(et_file, 'w')
    for ee_vector in ee_vectors:
        ee_fh.write("%s\n" % ee_vector)
    for et_vector in et_vectors:
        et_fh.write("%s\n" % et_vector)


def _create_vectors_for_sentence(tarsqidoc, element, s,
                                 ee_vectors, et_vectors):
    """Adds ee and et vectors in the sentence to ee_vectors and et_vectors."""
    _debug_leafnodes(element, s)
    tag_vectors = _get_tag_vectors_for_sentence(tarsqidoc, s)
    for i in range(0, len(tag_vectors) - 1):
        v1 = tag_vectors[i]
        v2 = tag_vectors[i+1]
        _debug("\n  %d %d %s %s\n" % (i, i + 1, v1.source, v2.source))
        if v1.is_event_vector() and v2.is_event_vector():
            ee_vector = EEVector(tarsqidoc, v1, v2)
            _debug_wrapped("EE %s" % ee_vector, '  ')
            ee_vectors.append(ee_vector)
        elif v1.is_event_vector() and v2.is_timex_vector():
            et_vector = ETVector(tarsqidoc, v1, v2)
            _debug_wrapped("ET %s" % et_vector, '  ')
            et_vectors.append(et_vector)
        elif v1.is_timex_vector() and v2.is_event_vector():
            et_vector = ETVector(tarsqidoc, v2, v1)
            _debug_wrapped("TE %s" % et_vector, '  ')
            et_vectors.append(et_vector)


def _get_tag_vectors_for_sentence(tarsqidoc, s):
    """Returns timex and event vectors for the sentence."""
    vectors = []
    for tag in sorted(s.events() + s.timexes()):
        identifier = tag.attrs.get(EIID, tag.attrs.get(TID))
        vector = make_vector(tarsqidoc, tag)
        vectors.append(vector)
    for v in vectors:
        _debug("  %s" % v.source)
    return vectors


def make_vector(tarsqidoc, tag):
    """Factory nethod to create a vector for an event tag or timex tag."""
    if tag.name == EVENT:
        return EventVector(tarsqidoc, tag)
    elif tag.name == TIMEX:
        return TimexVector(tarsqidoc, tag)
    else:
        return None


def compare_features(f1, f2):
    """Comparison method for feature sorting."""
    def get_prefix(feature):
        if feature.startswith('e1-'): return 'e1'
        if feature.startswith('e2-'): return 'e2'
        if feature.startswith('e-'): return 'e'
        if feature.startswith('t-'): return 't'
        return 'x'
    prefixes = {'e': 1, 't': 2, 'e1': 3, 'e2': 4}
    p1 = get_prefix(f1)
    p2 = get_prefix(f2)
    prefix_comparison = cmp(p1, p2)
    return cmp(f1, f2) if prefix_comparison == 0 else prefix_comparison


class Vector(object):

    def __init__(self, tarsqidoc, source, source_tag, features):
        self.source = source
        string = tarsqidoc.source.text[source.begin:source.end]
        self.features = {TAG: source_tag,
                         STRING: string}
        for feat in features:
            val = self.get_value(feat)
            # TODO: add "if val is not None:"?
            self.features[feat] = val

    def __str__(self):
        feats = []
        for feat in self.sorted_features():
            val = self.features[feat]
            feats.append("%s=%s" % (feat, val))
        return ' '.join(feats)

    def is_event_vector(self):
        return False

    def is_timex_vector(self):
        return False

    def sorted_features(self):
        return sorted(self.features.keys(), compare_features)


class EventVector(Vector):

    """Implements a vector with internal features of the event tag."""

    def __init__(self, tarsqidoc, event):
        super(EventVector, self).__init__(tarsqidoc, event, EVENT, EVENT_FEATURES)

    def is_event_vector(self):
        return True

    def get_value(self, attr):
        if attr == MODALITY:
            return self.source.attrs.get(attr, 'NONE')
        elif attr == POLARITY:
            return self.source.attrs.get(attr, 'POS')
        else:
            return self.source.attrs.get(attr)


class TimexVector(Vector):

    """Implements a vector with internal features of the timex tag."""

    def __init__(self, tarsqidoc, timex):
        super(TimexVector, self).__init__(tarsqidoc, timex, TIMEX, TIMEX_FEATURES)

    def is_timex_vector(self):
        return True

    def get_value(self, attr):
        return self.source.attrs.get(attr)


class PairVector(Vector):

    def __init__(self, prefix1, vector1, prefix2, vector2):
        self.source = (vector1.source, vector2.source)
        self.relType = 'UNKNOWN'
        self.features = {}
        self.v1 = vector1
        self.v2 = vector2
        for att, val in vector1.features.items():
            self.features["%s-%s" % (prefix1, att)] = val
        for att, val in vector2.features.items():
            self.features["%s-%s" % (prefix2, att)] = val

    def __str__(self):
        return "%s %s %s" % (self.identifier, self.relType,
                             super(PairVector, self).__str__())


class EEVector(PairVector):

    """Class responsible for creating the vector between two events. Uses the
    vector of each event and adds extra features. The result looks like:

       UNKNOWN e1-aspect=NONE e1-class=OCCURRENCE e1-epos=VERB e1-modality=NONE
       e1-polarity=POS e1-stem=None e1-string=stay e1-tag=EVENT
       e1-tense=INFINITIVE e2-aspect=NONE e2-class=OCCURRENCE e2-epos=VERB
       e2-modality=NONE e2-polarity=POS e2-stem=None e2-string=put e2-tag=EVENT
       e2-tense=PASTPART shiftAspect=0 shiftTense=1 """

    # TODO: features to add: distance (number or some kind of closeness binary
    # (more or less than three/five), surrounding tokens and tags, path to top,
    # conjunctions inbetween.

    def __init__(self, tarsqidoc, event_vector1, event_vector2):
        super(EEVector, self).__init__('e1', event_vector1, 'e2', event_vector2)
        tenses = [v.features.get(TENSE) for v in (self.v1, self.v2)]
        aspects = [v.features.get(ASPECT) for v in (self.v1, self.v2)]
        self.features[SHIFT_TENSE] = 0 if tenses[0] == tenses[1] else 1
        self.features[SHIFT_ASPECT] = 0 if aspects[0] == aspects[1] else 1
        self.identifier = "%s-%s-%s" % (os.path.basename(tarsqidoc.source.filename),
                                        self.v1.features.get(EIID),
                                        self.v2.features.get(EIID))


class ETVector(PairVector):

    """Class responsible for creating the vector between an event and a
    time. Uses the event and time vectors and adds extra features. The result
    looks like:

       UNKNOWN e-aspect=NONE e-class=OCCURRENCE e-epos=VERB e-modality=NONE
       e-polarity=POS e-stem=None e-string=put e-tag=EVENT e-tense=PASTPART
       t-string=2013 t-tag=TIMEX3 t-type=DATE t-value=2013 order=et
       signal=before """

    # TODO: fix the signal, this method now does the same as its predecessor,
    # which is nothing. Other features to add: distance (number or some kind of
    # closeness binary (more or less than three/five), surrounding tokens and
    # tags, path to top.

    def __init__(self, tarsqidoc, event_vector, timex_vector):
        super(ETVector, self).__init__('e', event_vector, 't', timex_vector)
        v1_begin = event_vector.source.begin
        v2_begin = timex_vector.source.begin
        self.features[ORDER] = 'et' if v1_begin < v2_begin else 'te'
        self.features[SIGNAL] = 'XXXX'
        self.identifier = "%s-%s-%s" % (os.path.basename(tarsqidoc.source.filename),
                                        self.v1.features.get(EIID),
                                        self.v2.features.get(TID))


def _debug(text):
    if DEBUG:
        print text


def _debug_wrapped(text, indent=''):
    if DEBUG:
        for line in textwrap.wrap(text, 100):
            print "%s%s" % (indent, line)

def _debug_leafnodes(element, s):
    if DEBUG:
        print("\n%s %s\n" % (element.begin, s))
        for n in s.leaf_nodes():
            print '  ', n

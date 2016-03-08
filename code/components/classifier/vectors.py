
from library.timeMLspec import EVENT, TIMEX, EID, EVENTID

# these should be defined in a library for classifier features
C_TID = 'tid'
C_TYPE = 'type'
C_VALUE = 'value'
C_FUNINDOC = 'functionInDoc'
C_TEMPFUN = 'temporalFunction'
C_EID = 'eid'
C_EIID = 'eiid'
C_STRING = 'string'
C_CLASS = 'Actualclass'
C_TENSE = 'tense'
C_ASPECT = 'aspect'
C_MOD = 'modality'
C_POL = 'negation'
C_TOE = 'timeorevent'
C_SHIFT_TENSE = 'shiftTen'
C_SHIFT_ASPECT = 'shiftAspect'
C_SIGNAL = 'Signal'

# The mappings below allow us to change the attributes in times and events
# without having to retrain everything since we can keep the features above
# unchanged (all that changes is how you get the value)..

EVENT_ATTRIBUTE_MAPPINGS = \
    [[C_EID, 'eid'], [C_EIID, 'eiid'], [C_CLASS, 'class'],
     [C_ASPECT, 'aspect'], [C_MOD, 'modality'], [C_POL, 'polarity'],
     [C_STRING, 'string'], [C_TENSE, 'tense'], [C_TOE, 'timeorevent']]

TIMEX_ATTRIBUTE_MAPPINGS = \
    [[C_TID, 'tid'], [C_TOE, 'timeorevent'], [C_STRING, 'string'],
     [C_FUNINDOC, 'functionInDoc'], [C_TEMPFUN, 'temporalFunction'],
     [C_TYPE, 'type'], [C_VALUE, 'value']]


def create_vectors(docelement, ee_file, et_file):
    """New method that takes over the functionality of the old
    Perl script named prepareClassifier."""

    object_vectors = []
    for event in docelement.tarsqi_tags.find_tags(EVENT):
        object_vectors.append(EventVector(docelement, event))
    for timex in docelement.tarsqi_tags.find_tags(TIMEX):
        object_vectors.append(TimexVector(docelement, timex))
    for v in object_vectors:
        print v.as_string()

    # mimic what was done in prepareClassifer, even though it seems moronic
    ee_file = open(ee_file, 'w')
    et_file = open(et_file, 'w')
    for i in range(0, len(object_vectors) - 1):
        v1 = object_vectors[i]
        v2 = object_vectors[i+1]
        if v1.is_event_vector() and v2.is_event_vector():
            ee_file.write(EEVector(v1, v2).as_string() + "\n")
        elif v1.is_event_vector() and v2.is_timex_vector():
            et_file.write(ETVector(v1, v2).as_string() + "\n")
        elif v1.is_timex_vector() and v2.is_event_vector():
            et_file.write(ETVector(v2, v1).as_string() + "\n")


class Vector:

    def is_event_vector(self):
        return False

    def is_timex_vector(self):
        return False

    def as_string(self, i=0):
        x = []
        for (name, attr) in self.mappings:
            x.append("%d%s-%s" % (i, name, self.get_value(attr)))
        return ' '.join(x)


class EventVector(Vector):

    def __init__(self, docelement, event):
        self.attrs = event.attrs
        self.attrs['string'] = docelement.doc.text(event.begin, event.end)
        self.mappings = EVENT_ATTRIBUTE_MAPPINGS

    def is_event_vector(self):
        return True

    def get_value(self, attr):
        if attr == 'modality':
            return self.attrs.get(attr, 'NONE')
        elif attr == 'timeorevent':
            return 'event'
        elif attr == 'polarity':
            # TODO: this is wrong
            return 'NONE' if self.attrs.get(attr, 'POS') == 'POS' else 'NEG'
        else:
            return self.attrs.get(attr, 'no_val')


class TimexVector(Vector):

    def __init__(self, docelement, timex):
        self.attrs = timex.attrs
        print self.attrs
        self.attrs['string'] = docelement.doc.text(timex.begin, timex.end)
        self.mappings = TIMEX_ATTRIBUTE_MAPPINGS

    def is_timex_vector(self):
        return True

    def get_value(self, attr):
        # TODO: this is wrong, but keep it for now
        if attr == 'temporalFunction':
            return 'time'
        elif attr == 'timeorevent':
            return 'NONE'
        elif attr == 'functionInDoc':
            return self.attrs.get(attr, 'false')
        elif attr == 'temporalFunction':
            return self.attrs.get(attr, 'time')
        else:
            return self.attrs.get(attr, 'no_val')


class EEVector:

    """Class responsible for creating the vector between two events. Uses
    the vectors of each event and creates three extra features:
    Signal, shiftAspect and shiftTen. The result looks like:

        UNKNOWN 0eid=e1 0Actualclass-OCCURRENCE 0aspect-NONE
        0modality-NONE # 0negation-NONE 0string-exploded 0te\nse-PAST
        0timeorevent-event # 0eid-e2 1Actualclass-OCCURRENCE
        1aspect-NONE 1modality-NONE # 1negation-NONE \1string-killing
        1tense-NONE 1timeorevent-event # Signal-NONE shiftAspect-0
        shiftTen-1"""

    def __init__(self, event_vector1, event_vector2):
        self.v1 = event_vector1
        self.v2 = event_vector2
        self.shiftAspect = 1
        self.shiftTen = 1
        if self.v1.get_value('tense') == self.v2.get_value('tense'):
            self.shiftTen = 0
        if self.v1.get_value('aspect') == self.v2.get_value('aspect'):
            self.shiftAspect = 0

    def as_string(self):
        return "UNKNOWN %s %s Signal-NONE %s-%d %s-%d" % \
            (self.v1.as_string(0), self.v2.as_string(1),
             C_SHIFT_ASPECT, self.shiftAspect, C_SHIFT_TENSE, self.shiftTen)


class ETVector:

    """Class responsible for creating the vector between an event and a
    time. Uses the event and time vectors and adds one extra feature:
    Signal. The result looks like:

        UNKNOWN 0Actualclass-OCCURRENCE 0aspect-NONE 0modality-NONE
        0negation-NONE 0string-killed 0tense-PAST 0timeorevent-event#
        1timeorevent-NONE 1string-Friday 1functionInDoc-false
        1temporalFunction-time 1type-DATE 1value-1998-08-07 Signal-NONE"""

    def __init__(self, event_vector, timex_vector):
        self.v1 = event_vector
        self.v2 = timex_vector

    def as_string(self):
        return "UNKNOWN %s %s Signal-NONE" % \
            (self.v1.as_string(0), self.v2.as_string(1))

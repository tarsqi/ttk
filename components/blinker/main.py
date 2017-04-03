"""Main module for Blinker, the rule-based Tlink generation component.

Responsible for loading the libraries and other top-level processing.

"""

import re

from utilities import logger
from library.tarsqi_constants import BLINKER
from library.main import LIBRARY
from library.blinker.blinker_rule_loader import BlinkerRuleDictionary
from components.common_modules.component import TarsqiComponent
from components.common_modules.tree import create_tarsqi_tree
from components.blinker.compare import compare_date


TIMEX = LIBRARY.timeml.TIMEX
TYPE = LIBRARY.timeml.TYPE
VALUE = LIBRARY.timeml.VALUE
EIID = LIBRARY.timeml.EIID
TID = LIBRARY.timeml.TID
LID = LIBRARY.timeml.LID
POL = LIBRARY.timeml.POL
TLINK = LIBRARY.timeml.TLINK
RELTYPE = LIBRARY.timeml.RELTYPE
ORIGIN = LIBRARY.timeml.ORIGIN
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
TIME_ID = LIBRARY.timeml.TIME_ID
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME


_DEBUG = False


# possible quotation marks; should be imported from elsewhere
QUOTES = ["``", '"', "'"]


class Blinker (TarsqiComponent):

    """Implements the Blinker component of Tarsqi. Blinker takes the shallow
    tree implemented in the TarsqiTree object and applies rules that capture
    regularities between events and times as well as between events.

    Instance variables:
       NAME         -  a string
       dct          -  document creation time: a string of the form YYYYMMDD
       rules        -  a BlinkerRuleDictionary
       rule2_index  -  a dictionary, quick access to type 2 rules
       tarsqidoc    -  a TarsqiDOcument
       doctree      -  a TarsqiTree"""

    def __init__(self, tarsqidoc):
        """Set component name and load rules into a BlinkerRuleDictionary
        object, this object knows where the rules are stored."""
        self.NAME = BLINKER
        self.dct = tarsqidoc.get_dct()
        self.tarsqidoc = tarsqidoc  # instance of TarsqiDocument
        self.doctree = None         # instance of TarsqiTree
        self.rules = BlinkerRuleDictionary()
        self._index_rules()
        # self.rules.pp_ruletype(3)

    def _index_rules(self):
        """Rules of type 2 (timex-signal-event) can be simply put in a hash
        keyed on the signals."""
        self.rule2_index = {}
        for rule in self.rules[2]:
            relation = rule.get_attribute('relation')[0]  # vals are now lists
            signal = rule.get_attribute('signal')[0]
            self.rule2_index[signal] = relation

    def run_timex_linking(self):
        """Apply the rules that govern relations between TIMEX3 tags. Only
        applies to TIMEX3 tags with type=DATE."""
        # TODO: add a DCT TIMEX tag if it is not in the tags dictionary, but
        # maybe check first whether it is in the dictionary in case we care
        # about duplications (see https://github.com/tarsqi/ttk/issues/10 and
        # https://github.com/tarsqi/ttk/issues/13)
        timexes = self.tarsqidoc.tags.find_tags(TIMEX)
        timexes = [t for t in timexes if t.attrs[TYPE] == 'DATE']
        pairs = _timex_pairs(timexes)
        for timex1, timex2 in pairs:
            try:
                self._create_timex_link(timex1, timex2)
            except Exception:
                # TODO: these are very common caused usually because one of the
                # timexes does not have a value, should look into this and
                # confirm this is always a GUTime issue.
                logger.warn("Error linking:\n%s\n%s" % (timex1, timex2))

    def _create_timex_link(self, timex1, timex2):
        """Try to create a TLINK between two timexes."""
        creation_year = self.dct[0:4]
        date1 = timex1.attrs.get(VALUE)
        date2 = timex2.attrs.get(VALUE)
        if date1 is None or date2 is None:
            logger.warning("Missing value in %s or %s" % (date1, date2))
            return
        date1 = _fix_timex_val(date1)
        date2 = _fix_timex_val(date2)
        tid1 = timex1.attrs['tid']
        tid2 = timex2.attrs['tid']
        origin = "%s-TimexLinking" % BLINKER
        if date1 == date2:
            if date1 not in ('PAST_REF', 'FUTURE_REF'):
                self._add_tlink('IDENTITY', tid1, tid2, origin)
        else:
            rel = compare_date(date1, date2, creation_year)
            if rel != 'IDENTITY':
                self._add_tlink(rel, tid1, tid2, origin)

    def process_element(self, element):
        """Apply the Blinker rules to the element. Creates a TarsqiTree instance
        and then applies the Blinker rules."""
        self.doctree = create_tarsqi_tree(self.tarsqidoc, element)
        self.docelement = element
        # self.pp_doctree(BLINKER)
        self._run_blinker()

    def _run_blinker(self):
        """Apply BLinker rules to the sentences in the doctree variable. This
        currently only deals with rule type 2, anchoring an event to a timex in
        those cases where there is a signal (that is, a preposition). New
        Tlinks are added just before the closing tag of the fragment."""

        self._apply_event_ordering_with_signal_rules()

        # variables needed for different rule types are prefixed with r<ruleNum>
        r3_event1 = None

        # iterate over sentences
        for si in range(len(self.doctree)):
            sentence = self.doctree[si]
            r3_main_event = None
            if _DEBUG:
                print "processing sentence", si

            # iterate over elements within a sentence
            for i in range(len(sentence)):
                element = sentence[i]
                timex = element.get_timex()
                event = element.get_event()
                # RULE TYPE 2
                if timex:
                    # chunk contains a timex, now try to anchor events to it
                    self._apply_event_anchoring_rules(sentence, timex, i)
                # RULE TYPE 3
                if event and element.isChunk() and element.isVerbChunk():
                    # the first verbal event in a sentence is considered the
                    # main event
                    if not r3_main_event:
                        r3_main_event = event
                        # if previous sentence contained an event, create a link
                        if r3_event1:
                            r3_event2 = r3_main_event
                            self._apply_type3_rules(r3_event1, r3_event2)
                            r3_event1 = r3_event2
                        # else set event1
                        else:
                            r3_event1 = r3_main_event
                # RULE TYPE 5
                if event and element.isChunk() \
                        and element.isVerbChunk() \
                        and event.attrs['class'] == 'REPORTING':
                    if _DEBUG:
                        print "applying type 5 rules"
                    self._apply_type5_rules(sentence, event, i)

            # R3: if no main event in sentence
            if not r3_main_event:
                r3_event1 = None


    def _apply_type3_rules(self, event1, event2):
        """ Creates a TLINK between two main events """
        if _DEBUG:
            _pp_events(event1, event2)
        for i in range(len(self.rules[3])):
            rule = self.rules[3][i]
            if _DEBUG:
                rule.pp()
            if event1.attrs['class'] in rule.attrs['arg1.class'] and \
               event2.attrs['class'] in rule.attrs['arg2.class'] and \
               event1.attrs['tense'] in rule.attrs['arg1.tense'] and \
               event2.attrs['tense'] in rule.attrs['arg2.tense'] and \
               event1.attrs['aspect'] in rule.attrs['arg1.aspect'] and \
               event2.attrs['aspect'] in rule.attrs['arg2.aspect']:
                self._add_tlink(rule.attrs['relation'][0],
                                event1.attrs[EIID],
                                event2.attrs[EIID],
                                "%s-Rule-%s" % (BLINKER, rule.id))
                if _DEBUG:
                    print "RULE %s fired!" % rule.rule_number
                return

    def _apply_type5_rules(self, sentence, event1, position):

        """ Creates TLINKs between the reporting event and reported events

        Takes as arguments sentence, reporting event constituent, and
        position of that constituent within the sentence list"""

        # filter out rules with wrong tense
        applicable_rules = self.rules[5][:]
        applicable_rules = [rule for rule in applicable_rules
                            if event1.attrs['tense'] in rule.attrs['arg1.tense']]

        # reset to opposite when quote is encountered
        # TODO: this whole business with direct is too verbose, simply use
        # True/False and "direct = not direct", but first get this stuff to work
        # and make test cases.
        direct = 'INDIRECT'

        # forward

        if _DEBUG:
            print "inside rule application function"
            sentence.pretty_print()
        for i in range(position+1, len(sentence)):
            if _DEBUG:
                print "processing element", i
            element = sentence[i]

            # quote
            if element.isToken() and element.getText() in QUOTES:
                if direct == 'DIRECT':
                    direct = 'INDIRECT'
                if direct == 'INDIRECT':
                    direct = 'DIRECT'

            # event
            event2 = element.get_event()
            if event2 and element.isChunk() and element.isVerbChunk():
                current_rules = applicable_rules[:]
                current_rules = [rule for rule in current_rules
                                 if direct in rule.attrs['sentType']]
                if _DEBUG:
                    _pp_events(event1, event2)
                for rule in current_rules:
                    # if attribute not set in the rule, accept any value
                    for att in ['class', 'tense', 'aspect']:
                        if 'arg2.'+att not in rule.attrs:
                            rule.attrs['arg2.'+att] = [event2.attrs[att]]
                    if _DEBUG:
                        rule.pp()
                    # check that specified values match
                    if event2.attrs['class'] in rule.attrs['arg2.class'] and \
                       event2.attrs['tense'] in rule.attrs['arg2.tense'] and \
                       event2.attrs['aspect'] in rule.attrs['arg2.aspect']:
                        self._add_tlink(rule.attrs['relation'][0],
                                        event1.attrs[EIID],
                                        event2.attrs[EIID],
                                        "%s-Rule-%s" % (BLINKER, rule.id))
                        if _DEBUG:
                            print "RULE %s fired!" % rule.rule_number
                        # apply the first matching rule
                        return

        # backward

        # - this creates multiple links for REPORTING to REPORTING
        # - may add the appropriate rules to the rule file instead
        direct = 'INDIRECT'
        for i in range(position-1, -1, -1):   # ..,3,2,1,0
            if _DEBUG:
                print "processing element", i
            element = sentence[i]

            # quote
            if element.isToken() and element.getText() in QUOTES:
                if direct == 'DIRECT':
                    direct = 'INDIRECT'
                if direct == 'INDIRECT':
                    direct = 'DIRECT'

            # event
            event2 = element.get_event()
            if event2 and element.isChunk() and element.isVerbChunk():
                current_rules = applicable_rules[:]
                current_rules = [rule for rule in current_rules
                                 if direct in rule.attrs['sentType']]
                if _DEBUG:
                    _pp_events(event1, event2)
                    print "Applying rules for sentence type:", \
                        direct, len(current_rules), "rules"
                for rule in current_rules:
                    # if attribute not set in the rule, accept any value
                    for att in ['class', 'tense', 'aspect']:
                        if 'arg2.'+att not in rule.attrs:
                            rule.attrs['arg2.'+att] = [event2.attrs[att]]
                    if _DEBUG:
                        print "RULE %s (%s):" % (rule.rule_number,
                                                 rule.attrs['sentType'][0])
                        print rule.attrs['arg1.class'], rule.attrs['arg1.tense'], \
                            rule.attrs['arg1.aspect']
                        print rule.attrs['arg2.class'], rule.attrs['arg2.tense'], \
                            rule.attrs['arg2.aspect']
                    # check that specified values match
                    if event2.attrs['class'] in rule.attrs['arg2.class'] and \
                       event2.attrs['tense'] in rule.attrs['arg2.tense'] and \
                       event2.attrs['aspect'] in rule.attrs['arg2.aspect']:
                        rel = rule.attrs['relation'][0]
                        origin = "BLINKER-Type5-rule%s" % rule.rule_number
                        self._add_tlink(rel,
                                        event1.attrs['eiid'],
                                        event2.attrs['eiid'],
                                        origin)
                        if _DEBUG:
                            print "RULE %s fired!" % rule.rule_number
                        # apply the first matching rule
                        return

    def _apply_event_anchoring_rules(self, sentence, timex, i):

        """Anchor events to a given timex that occurs in the sentence at index
        i. The method proceeds by looking for some simple syntactic patterns
        with and without prepositions. If a pattern with a preposition occurs,
        then the preposition is looked up in self.rule2_index. If no signal is
        found, then the default INCLUDES rule will apply (rule 1), this is not
        yet implemented."""

        # NOTES:
        # - Need to add some kind of confidence measures

        # PATTERN: [TIMEX EVENT]
        # Or, more precisely, an event in the same chunk as the timex
        # Example: "October elections"
        event = sentence[i].get_event()
        if event:
            eiid = event.attrs[EIID]
            tid = timex.attrs[TID]
            self._add_tlink('IS_INCLUDED', eiid, tid, "%s-Type-1" % BLINKER)
            return

        # Pattern: [CHUNK-WITH-EVENT] Prep [CHUNK-WITH-TIMEX]
        if i > 1:
            event = sentence[i-2].get_event()
            if sentence[i-1].isPreposition() and event:
                signal = sentence[i-1].getText().lower()
                rel = self.rule2_index.get(signal)
                eiid = event.attrs[EIID]
                tid = timex.attrs[TID]
                if _DEBUG:
                    print "FOUND: [%s] %s [%s] --> %s" % \
                        (event.dtrs[0].getText(), signal, timex.getText(), rel)
                self._add_tlink(rel, eiid, tid, "%s-Type-2-%s" % (BLINKER, signal))
                return

        # Pattern: [CHUNK-WITH-VERBAL-EVENT] [CHUNK-WITH_TIMEX]
        if i > 0:
            previous_chunk = sentence[i-1]
            if previous_chunk.isVerbChunk():
                event = previous_chunk.get_event()
                if event:
                    # if event.attrs[POL] != 'NEG':
                    eiid = event.attrs[EIID]
                    tid = timex.attrs[TID]
                    self._add_tlink('IS_INCLUDED', eiid, tid,
                                    "%s-Type-1a" % BLINKER)
                    return


    def _apply_event_ordering_with_signal_rules(self):

        """Some more rules without using any rules, basically a placeholder
        for event ordering rules that use a signal."""

        signal_mapping = {'after': 'AFTER',
                          'before': 'BEFORE',
                          'during': 'DURING'}

        for si in range(len(self.doctree)):
            sentence = self.doctree[si]
            for i in range(len(sentence)):
                try:
                    # print sentence[i:i+4]
                    (VG1, Prep, NG, VG2) = sentence[i:i+4]
                    event1 = VG1.get_event()
                    event2 = VG2.get_event()
                    # Pattern: [VG +Event] [Prep] [NG -Event] [VG +Event]
                    if event1 and VG1.isVerbChunk() and \
                            Prep.isPreposition() and \
                            NG.isNounChunk() and not NG.get_event() and \
                            event2 and VG2.isVerbChunk():
                        # print "[VG +Event] [Prep] [NG -Event] [VG +Event]"
                        # print Prep
                        prep_token = Prep.getText().lower()
                        # print prep_token
                        rel = signal_mapping.get(prep_token)
                        # print rel
                        if rel:
                            # print 'adding tlink'
                            eiid1 = event1.attrs[EIID]
                            eiid2 = event2.attrs[EIID]
                            self._add_tlink(rel, eiid1, eiid2,
                                            "%s-Event:Signal:Event" % BLINKER)
                except:
                    pass


    def _add_tlink(self, reltype, id1, id2, source):
        """Add a TLINK to self.tarsqidoc."""
        id1_attr = TIME_ID if id1.startswith('t') else EVENT_INSTANCE_ID
        id2_attr = RELATED_TO_TIME if id2.startswith('t') else RELATED_TO_EVENT_INSTANCE
        attrs = { LID: self.tarsqidoc.next_link_id(TLINK),
                  id1_attr: id1, id2_attr: id2,
                  RELTYPE: reltype, ORIGIN: source }
        self.tarsqidoc.tags.add_tag(TLINK, -1, -1, attrs)


def _timex_pairs(timexes):
    """Return a list of timex pairs where the first element occurs before the
    second element on the input list."""
    pairs = []
    for i in range(len(timexes)):
        for j in range(len(timexes)):
            if i < j:
                pairs.append([timexes[i], timexes[j]])
    return pairs


def _fix_timex_val(date):
    """Rather simplistic way to add in hyphens. There are probably a lot
    of cases it does not deal with."""
    match = re.compile("^(\d\d\d\d)(\d\d)(\d\d)(.*)").match(date)
    if match:
        (year, month, days, rest) = match.groups()
        return "%s-%s-%s%s" % (year, month, days, rest)
    match = re.compile("^(\d\d\d\d)(\d\d)(.*)").match(date)
    if match:
        (year, month, rest) = match.groups()
        return "%s-%s%s" % (year, month, rest)
    return date


def _pp_events(event1, event2):
    print(event1.dtrs[0].getText(), event2.dtrs[0].getText())
    print('   e1', event1.dtrs[0].getText(), event1.attrs['class'],
          event1.attrs['tense'], event1.attrs['aspect'])
    print('   e2', event2.dtrs[0].getText(), event2.attrs['class'],
          event2.attrs['tense'], event2.attrs['aspect'])

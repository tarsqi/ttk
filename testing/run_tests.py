"""run_tests.py

Simple tests that ping the Tarsqi components in various ways. There are tests
for the following things:

- is there a tag from offset1 to offset2
- is there not a tag from offset1 to offset2
- does the tag from offset1 to offset2 have an attribute X with value Y
- is a set of output constraints the same as the expected output

There are three possible results for a test: pass, fail or error.

These test are not intended for extensive testing of coverage.

Usage:

   $ python run_tests.py OPTIONS*

The following options are available:

   --gutime       run the GUTime tests
   --evita        run the Evita tests
   --slinket      run the Slinket tests
   --s2t          run the S2T tests
   --blinker      run the Blinker tests
   --sputlink     run the SputLink tests
   --show-errors  print the stack trace of all errors

If none of the first six options are given all test will run.

The tests are focussed on components, but most of the actual test cases focus on
tags, which allows for some flexibility. If for example a BTime component is
added we would create a new subclass of TarsqiEntityTest, similar to GUTimeTest,
but with a different pipeline, and then use this test in the initialization of
ModuleTest. We can use the same tests as for GUTime. But timex test cases could
be split into cases for BTime and GUTime if we wanted, all we need to do is edit
the case.test_case_timex module and the variables from it that are imported in
this script.

Examples:

   $ python run_tests.py --evita
   $ python run_tests.py --gutime --evita

An earlier version of this was done with UnitTest, but this way made it easier
to deal with reading an arbitrary number of tests from a file.

"""


import sys, getopt, traceback, types

import path
import tarsqi
from components.merging.sputlink.main import ConstraintPropagator

from cases.test_cases_timex import TIMEX_TESTS
from cases.test_cases_event import EVENT_TESTS
from cases.test_cases_slink import ALINK_TESTS
from cases.test_cases_slink import SLINK_TESTS
from cases.test_cases_tlink import S2T_TESTS
from cases.test_cases_tlink import BLINKER_TESTS
from cases.test_cases_sputlink import SPUTLINK_TESTS


PASS = 'ok'
FAIL = 'fail'
ERROR = 'error'

# this can be overruled with the --show-errors option
SHOW_ERRORS = False

GUTIME_PIPELINE = 'TOKENIZER,TAGGER,CHUNKER,GUTIME'
EVITA_PIPELINE = 'TOKENIZER,TAGGER,CHUNKER,EVITA'
SLINKET_PIPELINE = 'TOKENIZER,TAGGER,CHUNKER,GUTIME,EVITA,SLINKET'
S2T_PIPELINE = 'TOKENIZER,TAGGER,CHUNKER,EVITA,SLINKET,S2T'
BLINKER_PIPELINE = 'TOKENIZER,TAGGER,CHUNKER,GUTIME,EVITA,BLINKER'

# this is used when we run all tests so we can print a summary at the end
SUMMARY = []


class TarsqiTest(object):

    """The mother of all tests. Just an empty shell."""


class TarsqiEntityTest(TarsqiTest):

    """A test case for Tarsqi entities (events and times)."""

    def __init__(self, tag, test_specification):
        """Load the test specification from the cases module."""
        self.name = test_specification[0]
        self.sentence = test_specification[1]
        self.o1 = test_specification[2]
        self.o2 = test_specification[3]
        self.tag = tag
        self.find_tag = True
        self.attributes = []
        self.results = {PASS: 0, FAIL: 0, ERROR: 0}
        for specification_element in test_specification[4:]:
            if specification_element is None:
                self.find_tag = False
            elif isinstance(specification_element, types.TupleType):
                self.attributes.append(specification_element)

    def run(self, pipeline):
        """Run the entity test using the pipeline as handed in from the same
        method on subclasses. Results are written to the standard output."""
        try:
            td = run_pipeline(pipeline, self.sentence)
            tag = get_tag(td, self.tag, self.o1, self.o2)
            if self.find_tag:
                result = PASS if tag else FAIL
            else:
                result = PASS if tag is None else FAIL
            self.results[result] += 1
            entity_spec = "%s(%s:%s)=%s" % (self.tag, self.o1, self.o2, self.find_tag)
            print "  %-30s %-30s %s" % (self.name, entity_spec, result)
            for attr, val in self.attributes:
                attr_spec = "   %s=%s" % (attr, val.replace(' ', '_'))
                if result == PASS:
                    attr_result = PASS if tag.attrs.get(attr) == val else FAIL
                    self.results[attr_result] += 1
                    print "  %-30s %-30s %s" % (self.name, attr_spec, attr_result)
                else:
                    print "  %-30s %-30s %s" % (self.name, attr_spec, result)
        except:
            self.results[ERROR] += 1
            print "  %-61s %s" % (self.name, ERROR)
            if SHOW_ERRORS:
                print; traceback.print_exc(); print


class TarsqiLinkTest(TarsqiTest):

    """A test case for Tarsqi links (alinks, slinks and tlinks)."""

    def __init__(self, tag, test_specification):
        """Load the test specification from the cases module."""
        self.sentence = test_specification[5]
        self.linkname = tag
        self.filename = test_specification[1]
        self.rule = test_specification[2]
        self.reltype = test_specification[0]
        self.e1 = test_specification[3]
        self.e2 = test_specification[4]
        self.name = "%s-%s" % (self.reltype, self.rule)
        self.find_tag = True
        if len(test_specification) > 6:
            self.find_tag = test_specification[6]
        self.results = {PASS: 0, FAIL: 0, ERROR: 0}

    def run(self, pipeline):
        """Run the entity test using the pipeline as handed in from the same method on
        subclasses. Results are written to the standard output."""
        try:
            td = run_pipeline(pipeline, self.sentence)
            tag = get_link(td, self.linkname, self.e1, self.e2, self.reltype)
            if self.find_tag:
                result = PASS if tag else FAIL
            else:
                result = PASS if tag is None else FAIL
            self.results[result] += 1
            link_spec = "%s(%s:%s-%s:%s)=%s" \
                        % (self.reltype, self.e1[0], self.e1[1],
                           self.e2[0], self.e2[1], self.find_tag)
            print "  %-35s %-40s %s" % (self.name, link_spec, result)
        except:
            self.results[ERROR] += 1
            print "  %-76s %s" % (self.name, ERROR)
            if SHOW_ERRORS:
                print; traceback.print_exc(); print


class GUTimeTest(TarsqiEntityTest):
    """Test case for GUTime tests. This test is handed the test specifications
    and uses TarsqiEntityTest with the 'TIMEX3' tag and the GUTime pipeline."""

    def __init__(self, test_specification):
        TarsqiEntityTest.__init__(self, 'TIMEX3', test_specification)

    def run(self):
        TarsqiEntityTest.run(self, GUTIME_PIPELINE)


class EvitaTest(TarsqiEntityTest):
    """Test case for GUTime tests. This test is handed the test specifications
    and uses TarsqiEntityTest with the 'EVENT' tag and the Evita pipeline."""

    def __init__(self, test_specification):
        TarsqiEntityTest.__init__(self, 'EVENT', test_specification)

    def run(self):
        TarsqiEntityTest.run(self, EVITA_PIPELINE)


class SlinketTest(TarsqiLinkTest):
    """Test case for Slinket tests. This test is handed the test specifications and
    the link tag and uses TarsqiLinkTest with the Slinket pipeline."""

    def __init__(self, tag, test_specification):
        TarsqiLinkTest.__init__(self, tag, test_specification)

    def run(self):
        TarsqiLinkTest.run(self, SLINKET_PIPELINE)


class S2TTest(TarsqiLinkTest):
    """Test case for S2T tests. This test is handed the test specifications and
    the link tag and uses TarsqiLinkTest with the S2T pipeline."""

    def __init__(self, tag, test_specification):
        TarsqiLinkTest.__init__(self, tag, test_specification)

    def run(self):
        TarsqiLinkTest.run(self, S2T_PIPELINE)


class BlinkerTest(TarsqiLinkTest):
    """Test case for Blinker tests. This test is handed the test specifications and
    the link tag and uses TarsqiLinkTest with the Blinker pipeline."""

    def __init__(self, tag, test_specification):
        TarsqiLinkTest.__init__(self, tag, test_specification)

    def run(self):
        TarsqiLinkTest.run(self, BLINKER_PIPELINE)


class SputLinkTest(TarsqiTest):

    def __init__(self, test_specification):
        self.name = test_specification.description
        self.input = test_specification.constraints
        self.output = test_specification.result
        self.results = {PASS: 0, FAIL: 0, ERROR: 0}

    def run(self):
        """Run the SputLink test by directly accessing the ConstrainPropagator
        and checking the resulting constraints. Results are written to the
        standard output and stored in a variable."""
        try:
            cp = ConstraintPropagator(constraints=self.input)
            cp.queue_test_constraints(self.input)
            cp.propagate_constraints()
            cp.close_cycle_debug_file()
            edges = cp.collect_edges()
            observed_output = []
            for edge in edges:
                constraint = (edge.node1, edge.constraint.relset, edge.node2)
                observed_output.append(constraint)
            result = sorted(self.output) == sorted(observed_output)
            result = PASS if result else FAIL
            self.results[result] += 1
            print "  %-35s %s" % (self.name, result)
        except:
            self.results[ERROR] += 1
            print "  %-76s %s" % (self.name, ERROR)
            if SHOW_ERRORS:
                print; traceback.print_exc(); print


def run_pipeline(pipeline, sentence):
    """Run the sentence through the pipeline and return the resulting
    TarsqiDocument. The process_string method does not trap errors."""
    return tarsqi.process_string(sentence, pipeline=pipeline, loglevel=1)


def get_tag(td, tag, o1, o2):
    """Return the tag between offsets o1 and o2 if there is one, return None if
    there is no such tag."""
    tags = td.tags.find_tags(tag)
    for t in tags:
        if t.begin == o1 and t.end == o2:
            return t
    return None


def get_link(td, tagname, t1_offsets, t2_offsets, reltype):
    """Return the link tag with the specified tagname (SLINK, ALINK or TLINK),
    relation type and event locations. Return None if there is no such link"""
    link_tags = td.tags.find_tags(tagname)
    event_tags = td.tags.find_tags('EVENT')
    timex_tags = td.tags.find_tags('TIMEX3')
    for link_tag in link_tags:
        # print link_tag
        if tagname == 'ALINK':
            id1 = link_tag.attrs['eventInstanceID']
            id2 = link_tag.attrs['relatedToEventInstance']
        elif tagname == 'SLINK':
            id1 = link_tag.attrs['eventInstanceID']
            id2 = link_tag.attrs['subordinatedEventInstance']
        elif tagname == 'TLINK':
            id1 = link_tag.attrs.get('eventInstanceID') \
                or link_tag.attrs.get('timeID')
            id2 = link_tag.attrs.get('relatedToEventInstance') \
                or link_tag.attrs.get('relatedToTime')
            # print id1, id2
        relType = link_tag.attrs['relType']
        t1 = select_event(id1, event_tags) \
            if id1.startswith('e') \
            else select_timex(id1, timex_tags)
        t2 = select_event(id2, event_tags) \
            if id2.startswith('e') \
            else select_timex(id2, timex_tags)
        if (t1.begin == t1_offsets[0] and t1.end == t1_offsets[1] and
            t2.begin == t2_offsets[0] and t2.end == t2_offsets[1] and
            relType == reltype):
            return link_tag
    return None


def select_event(eiid, event_tags):
    for event_tag in event_tags:
        if event_tag.attrs['eiid'] == eiid:
            return event_tag
    return None


def select_timex(tid, timex_tags):
    for timex_tag in timex_tags:
        if timex_tag.attrs['tid'] == tid:
            return timex_tag
    return None


class ModuleTest(object):

    """The class that implements a module test. It is given a module name, the
    module test class, a list of test specifications, and an optional tagname
    that is tested. When running a module test you will run al test cases from
    the test specifications list."""

    def __init__(self, module_name, module_class, test_specs, tag=None):
        self.module_name = module_name
        self.module_class = module_class
        self.test_specifications = test_specs
        self.tag = tag

    def run(self):
        print "\n>>> Running %s Tests...\n" % self.module_name
        results = {PASS: 0, FAIL: 0, ERROR: 0}
        for test_specification in self.test_specifications:
            if self.tag:
                test = self.module_class(self.tag, test_specification)
            else:
                test = self.module_class(test_specification)
            test.run()
            results[PASS] += test.results[PASS]
            results[FAIL] += test.results[FAIL]
            results[ERROR] += test.results[ERROR]
        p, f, e = results[PASS], results[FAIL], results[ERROR]
        print "\nTOTALS:  PASS=%s  FAIL=%s  ERROR=%s\n" % (p, f, e)
        SUMMARY.append([self.module_name, p, f, e])


def test_all():
    test_gutime()
    test_evita()
    test_slinket()
    test_s2t()
    test_blinker()
    test_sputlink()
    print_summary()


def test_gutime():
    ModuleTest('GUTime', GUTimeTest, TIMEX_TESTS).run()


def test_evita():
    ModuleTest('Evita', EvitaTest, EVENT_TESTS).run()


def test_slinket():
    ModuleTest('Slinket Alink', SlinketTest, ALINK_TESTS, 'ALINK').run()
    ModuleTest('Slinket Slink', SlinketTest, SLINK_TESTS, 'SLINK').run()


def test_s2t():
    ModuleTest('S2T', S2TTest, S2T_TESTS, 'TLINK').run()


def test_blinker():
    ModuleTest('Blinker', BlinkerTest, BLINKER_TESTS, 'TLINK').run()


def test_sputlink():
    ModuleTest('SputLink', SputLinkTest, SPUTLINK_TESTS).run()


def print_summary():
    print "\nSUMMARY:\n"
    print "   %-15s    %-10s  %-10s  %s" % ('', ' PASS', ' FAIL',  'ERROR')
    for module, p, f, e in SUMMARY:
        print "   %-15s    %5s       %5s       %5s" % (module, p, f, e)
    print
    if f or e:
        print "   THERE WERE FAILURES OR ERRORS\n"


if __name__ == '__main__':

    # a dummy run just to get the tagger messages out of the way
    tarsqi.process_string("Fido barks.")

    run_gutime_tests = False
    run_evita_tests = False
    run_slinket_tests = False
    run_s2t_tests = False
    run_blinker_tests = False
    run_sputlink_tests = False

    components = ['evita', 'gutime', 'slinket', 's2t', 'blinker', 'sputlink']
    opts, args = getopt.getopt(sys.argv[1:], '', components + ['show-errors'])
    for opt, val in opts:
        if opt == '--show-errors': SHOW_ERRORS = True
        if opt == '--evita': run_evita_tests = True
        if opt == '--gutime': run_gutime_tests = True
        if opt == '--slinket': run_slinket_tests = True
        if opt == '--s2t': run_s2t_tests = True
        if opt == '--blinker': run_blinker_tests = True
        if opt == '--sputlink': run_sputlink_tests = True

    if not (run_gutime_tests or run_evita_tests or run_slinket_tests or
            run_s2t_tests or run_blinker_tests or run_sputlink_tests):
        test_all()
    else:
        if run_gutime_tests: test_gutime()
        if run_evita_tests: test_evita()
        if run_slinket_tests: test_slinket()
        if run_s2t_tests: test_s2t()
        if run_blinker_tests: test_blinker()
        if run_sputlink_tests: test_sputlink()

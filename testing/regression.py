"""regression.py

Regression test for the Tarsqi components. Currently only for Evita and within
evita only loads some verbal event cases.

Usage:

$ python regression.py --evita

   Runs all available Evita tests and stores the results in directories
   results/evita-XX where the XX denotes a particular Evita test. Files in the
   results directories are timestamped.

$ python regression.py --report

   Generate HTML reports of all available tests.

$ python regression.py --purge TEST_CASE TIMESTAMP

   Purge the resuts data for a particular test case at a particular timestamp
   and update the report. An example test case would be evita-vg.

$ python regression.py --create-event-vg-cases

   Creates test cases from cases/input/timebank-events-vg.txt and puts them in
   cases/cases-evita-vg.tab. This needs to be run only once.

Each line in a file with test cases represents one case, where a case is a
single string associated with two offsets. The line is tab-separated and has the
following fields:

   identifier string start_offset end_offset

The tagname of the tag spanning the offsets is filled in by the functions
testing a particular component.

The results files have the identifier and the associated test results and
indicate whether a tag was found at the indicated offsets. Results are + or -.

"""


import os, sys, getopt, time, glob

import path
import tarsqi

def load_cases(fname):
    """return a list of all test cases in fname."""
    cases = []
    for line in open(fname):
        if line[0] == '#': continue
        if not line.strip(): continue
        identifier, sentence, o1, o2 = line.strip().split("\t")
        o1 = int(o1)
        o2 = int(o2)
        cases.append(Case(identifier, sentence, o1, o2))
    print "Loaded %d test cases from fname" % len(cases)
    return cases


class Case(object):

    def __init__(self, identifier, sentence, o1, o2):
        self.identifier = identifier
        self.sentence = sentence
        self.o1 = o1
        self.o2 = o2

    def __str__(self):
        s = self.sentence
        o1 = self.o1
        o2 = self.o2
        return "%s [%d:%d] -- %s[%s]%s" \
            % (self.identifier, o1, o2, s[:o1], s[o1:o2], s[o2:])


def create_name_generator(names):
    """Creates a function that generates unique names given an input string"""
    def name_generator(name):
        name = '-'.join(name.split())
        names.setdefault(name,0)
        names[name] += 1
        name = "%s-%02d" % (name, names[name])
        return name
    return name_generator

def create_event_vg_cases():
    """Create cases for verbal events, using timebank-events-vg.txt."""
    name_generator = create_name_generator({})
    infile = 'testing/cases/input/timebank-events-vg.txt'
    outfile = 'testing/cases/cases-evita-vg.txt'
    out = open(outfile, 'w')
    out.write("# EVITA TEST CASES FOR VERBAL EVENTS\n")
    out.write("# Created by create_event_vg_cases() in testing/regression.py\n\n")
    for line in open(infile):
        if line[0] == '#': continue
        if not line.strip(): continue
        (chunkclass, verbgroup, sentence, offsets) = line.split("\t")
        # calculate the offsets by matching the verbgroup
        if verbgroup.find("n't") > -1:
            verbgroup = verbgroup.replace(" n't", "n't")
        # these are the offsets of the verbgroup
        o1 = sentence.find(verbgroup)
        o2 = o1 + len(verbgroup)
        vg = sentence[o1:o2]
        # now get the offsets of the head
        last_token_length = len(vg.split()[-1])
        o1 = o2 - last_token_length
        name = name_generator("%s-%s" % (chunkclass, vg))
        out.write("VG-%s\t%s\t%s\t%s\n" % (name, sentence, o1, o2))
    print "Created", outfile

def run_evita():
    load_tagger()
    cases = load_cases('testing/cases/cases-evita-vg.tab')
    outfile = "testing/results/evita-vg/%s.tab" % timestamp()
    fh = open(outfile, 'w')
    true = 0
    false = 0
    for case in cases:
        result = check_tag('PREPROCESSOR,EVITA', case.sentence, 'EVENT', case.o1, case.o2)
        fh.write("%s\t%s\n" % (case.identifier, '+' if result is True else '-'))
        if result is True:
            true += 1
        else:
            false += 1
    print "True=%s False=%s" % (true, false)

def check_tag(pipeline, sentence, tag, o1, o2):
    """Return True if sentence has tag between offsets o1 and o2."""
    # NOTE: apart from the options this is the same function as in unittests.py
    td = tarsqi.process_string(sentence, pipeline=pipeline, loglevel='1')
    tags = td.tags.find_tags(tag)
    for t in tags:
        if t.begin == o1 and t.end == o2:
            return True
    return False, tags

def load_tagger():
    # a dummy run just to get the tagger messages out of the way
    #tarsqi.process_string("Fido barks.", [('--pipeline', 'PREPROCESSOR')])
    tarsqi.process_string("Fido barks.", pipeline='PREPROCESSOR')

def timestamp():
    return time.strftime('%Y%m%d-%H%M%S')


class ReportGenerator(object):

    def __init__(self):
        self.cases_dir = 'testing/cases'
        self.results_dir = 'testing/results'
        self.html_dir = 'testing/results/html'
        self.index_file = os.path.join(self.html_dir, 'index.html')
        self.index_fh = open(self.index_file, 'w')
        self.cases = []
        self._init_cases()
        # the following are reset for each case
        self.case = None
        self.case_input_file = None
        self.case_input_fh = None
        self.case_input = None
        self.case_fh = None
        self.case_fh = None
        self.case_results = None

    def _init_cases(self):
        for name in glob.glob(self.cases_dir + '/cases-*.tab'):
            case_name = os.path.splitext(os.path.basename(name))[0]
            case_name = case_name[6:]
            #print case_name
            self.cases.append(case_name)

    def write_index(self):
        """Create the idex for all results."""
        self.index_fh.write("<html>\n<body>\n")
        for name in self.cases:
            self.index_fh.write("<a href=cases-%s.html>%s</a>\n" % (name, name))
        self.index_fh.write("</body>\n</html>\n")

    def write_cases(self):
        """Create the file with results for all cases."""
        for case in self.cases:
            self.case = case
            self.case_file = os.path.join(self.html_dir, "cases-%s.html" % case)
            self.case_fh = open(self.case_file, 'w')
            print "writing", self.case_file
            self._load_cases()
            self._load_case_results()
            self._write_case_report()

    def _load_cases(self):
        self.case_input_file = "%s/cases-%s.tab" % (self.cases_dir, self.case)
        self.case_input_fh = open(self.case_input_file)
        print "  reading cases in", self.case_input_file
        self.case_input = {}
        for case in load_cases(self.case_input_file):
            self.case_input[case.identifier] = case

    def _load_case_results(self):
        self.case_results = {}
        for results_file in glob.glob("%s/%s/*.tab" % (self.results_dir, self.case)):
            print '  reading results from', results_file
            timestamp = os.path.splitext(os.path.basename(results_file))[0]
            self.case_results[timestamp] = {}
            for line in open(results_file):
                (identifier, result) = line.strip().split("\t")
                self.case_results[timestamp][identifier] = result

    def _write_case_report(self):
        timestamps = sorted(self.case_results.keys())
        identifiers = {}
        for ts in timestamps:
            for identifier in self.case_results[ts].keys():
                identifiers[identifier] = True
        self.case_fh.write("<html>\n</body>\n")
        self.case_fh.write("<head>\n<style>\n")
        self.case_fh.write(".tag { color: blue; xfont-weight: bold; }\n")
        self.case_fh.write("</style>\n</head>\n")
        self.case_fh.write("<table cellpadding=5 cellspacing=0 border=1>\n")
        self.case_fh.write("<tr>")
        self.case_fh.write("  <td>&nbsp;")
        for ts in timestamps:
            self.case_fh.write("  <td>%s" % ts[2:8])
        self.case_fh.write("  <td>o1")
        self.case_fh.write("  <td>o2")
        self.case_fh.write("  <td>sentence")
        for identifier in sorted(identifiers.keys()):
            self.case_fh.write("<tr style=\"white-space:nowrap\">")
            self.case_fh.write("  <td>%s" % identifier)
            for ts in timestamps:
                self.case_fh.write("  <td>%s" % self.case_results[ts].get(identifier, '&nbsp;'))
            case = self.case_input[identifier]
            self.case_fh.write("  <td align=right>%s" % case.o1)
            self.case_fh.write("  <td align=right>%s" % case.o2)
            self.case_fh.write("  <td>%s<span class=\"tag\">%s</span>%s"
                               % (case.sentence[:case.o1],
                                  case.sentence[case.o1:case.o2],
                                  case.sentence[case.o2:]))
        self.case_fh.write("</table>")


def generate_report():
    """Generate the html reports from the current result files."""
    generator =  ReportGenerator()
    generator.write_index()
    generator.write_cases()

def purge_result(args):
    """Delete the results of one particular run of a case, the args parameter is
    a list of a case identifier and a timestamp, for example ['evita-vg',
    '20151124-171435']. This method will also regenerate the reports if a
    results file was actually removed.."""
    case, timestamp = args[0], args[1]
    report_generator = ReportGenerator()
    results_file = os.path.join(report_generator.results_dir,
                                case, "%s.tab" % timestamp)
    results_file_was_removed = False
    if os.path.isfile(results_file):
        print "Remove %s? (y/n)" % results_file
        print "?",
        answer = raw_input()
        if answer.strip() == 'y':
            os.remove(results_file)
            results_file_was_removed = True
    else:
        print "Warning: incorrect case or timestamp"
    if results_file_was_removed:
        generate_report()


if __name__ == '__main__':

    options = ['create-event-vg-cases', 'evita', 'report', 'purge']
    opts, args = getopt.getopt(sys.argv[1:], '', options)
    if not opts:
        exit("Nothing to do")
    for opt, val in opts:
        if opt == '--create-event-vg-cases': create_event_vg_cases()
        elif opt == '--evita': run_evita()
        elif opt == '--gutime': run_gutime()
        elif opt == '--report': generate_report()
        elif opt == '--purge': purge_result(args)

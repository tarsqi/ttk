import os
import sys
import unittest

#from tarsqi import TarsqiControl
from testing.common import load_mappings
from utilities.file import write_text_to_file
from utilities.file import file_contents

from testing.common import TESTCASES_DIR
from testing.common import REPORTS_DIR
from testing.common import DATA_DIR


TESTCASES = {}

tarsqi_class = None

if not TESTCASES:
    gutime_testcase_file = os.path.join(TESTCASES_DIR, 'gutime', 'gutime-cases.txt')
    TESTCASES = load_mappings(gutime_testcase_file)


class TestGutime(unittest.TestCase):

    """This class implements the test case for Gutime."""

    def run_test(self, id):

        print '  testcase ', id
        description = TESTCASES[id]['description']
        test_input = TESTCASES[id]['input']
        expected_output = TESTCASES[id]['output']

        infile_name = DATA_DIR + os.sep + 'input.xml'
        outfile_name = DATA_DIR + os.sep + 'output.xml'
        write_text_to_file(test_input, infile_name)

        options = {'pipeline': 'GUTIME'}
        #TarsqiControl('simple-xml', options, infile_name, outfile_name).process()
        tarsqi_class('simple-xml', options, infile_name, outfile_name).process()
        observed_output = file_contents(outfile_name)

        #expected_output = normalize_whitespace(expected_output)
        #observed_output = normalize_whitespace(observed_output)

        if expected_output != observed_output:
            errors_dir = os.path.join(REPORTS_DIR , 'gutime', 'errors')
            f1_name = id + '-expected.xml'
            f2_name = id + '-observed.xml'
            f1 = open(errors_dir + os.sep + f1_name, 'w')
            f2 = open(errors_dir + os.sep + f2_name, 'w')
            f1.write("<FILE>\n<NAME>%s</NAME>\n%s\n</FILE>\n" %
                     (f1_name, expected_output))
            f2.write("<FILE>\n<NAME>%s</NAME>\n%s\n</FILE>\n" %
                     (f2_name, observed_output))
            f1.close()
            f2.close()
            
        self.assertEqual(expected_output, observed_output, description)


    def test_001(self): self.run_test('001')
    def test_002(self): self.run_test('002')



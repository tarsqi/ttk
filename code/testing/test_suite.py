import os
import sys
import time
import unittest

from utilities import logger
from testing.common import REPORTS_DIR

import testing.test_gutime
import testing.test_evita



class TarsqiTest:

    """A TarsqiTest takes care of loading test cases from a TestCase and
    collecting them into a TestSuite. It then uses a TextTestRunner to
    run the loaded test cases.

    Instance variables:
       name - a string
       suite - a TestSuite"""
    
    def __init__(self, name, testcase):
        """Initialization sets the name and build the TestSuite."""
        self.name = name
        self.suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        
    def run(self):
        """Run the TestSuite."""
        print "Running %s test suite..." % self.name
        self._cleanup()

        fh = open(REPORTS_DIR + os.sep + self.name + os.sep + 'report.txt', 'w')
        fh.write("Running tests for %s at %d\n\n" % (self.name, time.time()))
        unittest.TextTestRunner(stream=fh, verbosity=2).run(self.suite)

    def _cleanup(self):
        """Cleanup the directory with error the reports."""
        for root, dirs, files in os.walk(REPORTS_DIR):
            if root.endswith(self.name + os.sep + 'errors'):
                for file in files:
                    path = root + os.sep + file
                    if path.endswith('.xml'):
                        os.remove(path)
                    

def main(tarsqi_control_class):
    
    """Run all Tarsqi test suites. It is called from tarsqi.py and
    handed as its sole argument the TarsqiControl class, which in turn
    is handed over to individual tests. The reson for this is that
    importing TarsqiCOntrol into the test suite introduced import
    errors for the analyse.py script."""

    logger.set_stdout_printing(False)
    
    testing.test_gutime.tarsqi_class = tarsqi_control_class
    TarsqiTest('gutime', testing.test_gutime.TestGutime).run()

    #testing.test_evita.tarsqi_class = tarsqi_control_class
    #TarsqiTest('evita', TestEvita).run()

    logger.set_stdout_printing(True)



        

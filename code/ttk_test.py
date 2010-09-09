"""

Main driver for the Tarsqi Unit Test. User specifies a list of modules
(currently accepts members of ['gutime', 'evita', 'slinket', 's2t',
'blinker']) and a list of file types (from ['timebank', 'rte3',
'simple-xml']). This driver builds the correct set of TestCase
objects, gives them to a TestSuite object, and then runs the TestSuite
using an instance of the TarsqiResult class, which writes the results
of the test to the report file.

Also includes code to help quickly create test cases that implement
regression tests.

NOTE: file types now restricted to simple-xml (MV 08/12/08)


USAGE 1:

    % ttk_test.py run <MOD_LIST|'all'|'none'> <TYPE_LIST|'all'>

    MOD_LIST and TYPE_LIST are comma separated lists of module names or file
        type names. Specifying 'all' tells ttk_test to run on every module or
        every file type. 'none' causes ttk_test to mot run on any of the
        modules, and instead just perform the function tests (not yet
        implemented).

For example, the command line:

    python ttk_test.py run gutime,blinker timebank
        will run only the unit tests for gutime and blinker, and only on the
        test cases that are timebank files, and the line:
    python ttk_test.py run all all
        will run all of the modules' unit tests, and will test all three
        file types, while
    python ttk_test.py run none all
        will run none of the module unit tests.

        
USAGE 2:

    % ttk_test.py create <definition_file> <directory>

        
"""


import sys
import time
from os import path
from os import remove
from unittest import TestSuite
from unittest import TestResult
from unittest import TestCase

from ttk_path import TTK_ROOT
from testing_new import module_tests
from testing_new.create_suites import create_suites


def buildSuite(modules,types):
    """
    Reads the user's input and builds the correct TestSuite, then runs it.

    Arguments:
        modules - string: comma-separated list of module names, 'all', or 'none'
        types- string: comma-separated list of file types, or 'all'

    """
    ACCEPTED_COMPONENT_NAMES = 'preprocessor,gutime,evita,slinket,s2t,blinker'
    
    # Instantiate a TestSuite object:
    suite=TestSuite()

    # Evaluate the 'all' and 'none' inputs:
    if modules == 'all':
        modules = ACCEPTED_COMPONENT_NAMES
    if modules == 'none':
        modules = ''

    # Get the current time as a string in the format
    # YYYY-MM-DD-HH-MM. It will be used for the report file's name as
    # well as for the directory used by the module reports.
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")

    # For each module the user selects, find the place in file_suite,
    # then get the right module suite file, and create the test case:
    for module in modules.split(','):
        if module in ACCEPTED_COMPONENT_NAMES.split(','):
            # Instantiate a ModuleTest and give it what it needs
            test=module_tests.ModuleTest()
            test.timestamp=timestamp
            test.types=types
            test.module=module
            # Add it to the TestSuite
            suite.addTest(test)
        
    # Instantiate a TarsqiResult:
    result=TarsqiResult(timestamp)
    # Run the TestSuite using the TarsqiResult we just created: 
    suite.run(result)
    # Tell the result object to perform its final bookkeeping:
    result.completeReport()
    # Update the log file with the current time and the location of the
    # report file:
    logFile=file(path.join(TTK_ROOT,'testing_new','logfile.txt'),'a')
    logFile.write("<TARSQITEST date='%s' location='%s' />\n" %(timestamp,result.reportpath) )
    logFile.close()



class TarsqiResult(TestResult):

    """
    A TarsqiResult is the object that when the TestSuite is run, takes the
    results of each module's individual unit test and writes the results into
    the report file.

    Instance Variables:
        failures - list of failures
        errors - list of errors
        testsRun - int
        shouldStop - int (unittest internal. unused here)
        reportname - string: the name the reportfile will be given
        reportpath - string: the full path to the reportfile
    """


    def __init__(self,reportname):
        """
        Initializes the TarsqiResult object and creates the report file, naming
        it based on the current system time.

        Arguments:
        """
        # from superclass init method:
        self.failures = []
        self.errors = []
        self.testsRun = 0
        self.shouldStop = 0

        # The report name is passed down from above. Here, we append the txt
        # extansion and constuct the complete path to the report file:
        self.reportname=reportname+".txt"
        self.reportpath=path.join(TTK_ROOT,'testing_new','reports',self.reportname)

        # Open the report file for the first time, creating a new file (or
        # overwriting if that file name already exists:
        reportfile=file(self.reportpath,'w')
        # Write the top of the report file: outermost tag and bookkeeping info: 
        headertext = "<TARSQITEST>\n<INFO date='%s' />\n\n" %(reportname)
        reportfile.write(headertext)
        reportfile.close()


    def addFailure(self,test,err):
        """
        The individual module tests will end in failure if any cases within them
        ended with either failures or errors. So this method displays how many
        ended in failure and how many ended in error, then writes the data into
        the report file
        """
        # Find out how many test cases ended in failure or in error: 
        numOfFails=len(test.result.failures)
        numOfErrors=len(test.result.errors)
        # Display the information:
        if numOfFails > 0:
            print "%i failures while testing module %s" %(numOfFails,test.module)
        if numOfErrors > 0:
            print "%i errors while testing module %s" %(numOfErrors,test.module)
        # Open the module test's report file and read it to memory:
        moduleReportFile=file(test.result.reportpath,'r')
        moduleReport=moduleReportFile.read()
        moduleReportFile.close()
        # Delete the file that holds the module report:
        remove(test.result.reportpath)
        # Open the Tarsqi test report file and append the contents of the
        # module test report:
        thisReportFile=file(self.reportpath,'a')
        thisReportFile.write(moduleReport)
        thisReportFile.write('\n\n')
        thisReportFile.close()

        
    def addError(self,test,err):
        """
        If the Tarsqi test TestSuite creates an error (which is what this method
        handles), it indicates that the code that runs the Tarsqi test (somewher
        between ttk_test.py, module_tests.py and test_results.py) has failed to
        execute properly.
        Conversely, if an error is called by one of the module tests and is
        recorded by the above method,it indicates that the code that runs Tarsqi
        (or perhaps testing.compare.py) has failed to execute properly.
        Therefore, this method simply takes the error text and records it in
        the report file as a "TESTINGERROR".
        """
        # Display:
        print "Error in TTK_TEST while testing module %s" %(test.module)
        # This is the text that will be added to the report file:
        text="<TESTINGERROR module='%s'> %s </TESTINGERROR>\n\n" %(test.module,err[1])
        # Open the report file and add the error message:
        thisReportFile=file(self.reportpath,'a')       
        thisReportFile.write(text)
        thisReportFile.close()
        

    def addSuccess(self,test):
        """
        If the module test runs, and none of the cases result in errors or
        failures, then the module has passed and this method runs. It displays
        a message indicating success, and copies the contents of the method
        test report (which is simply a list of "file A passed, file B passed..")
        into the Tarsqi test report.
        """
        # Display happy message:
        print "Module %s passed testing" %(test.module)
        # Read the contents of the module test report:
        moduleReportFile=file(test.result.reportpath,'r')
        moduleReport=moduleReportFile.read()
        moduleReportFile.close()
        # Delete the temporary file which contains the module report:
        remove(test.result.reportpath)
        # Write them to the Tarsqi test report.
        thisReportFile=file(self.reportpath,'a')
        thisReportFile.write(moduleReport)
        thisReportFile.write('\n\n')
        thisReportFile.close()       

        
    def addReport(self,funcName,errorList):
        """
        We also want to be able to write additional information into the
        Tarsqi test report. Since the TarsqiReport object holds the path to the
        report file, we add a method here to append other information to the
        report (Specifically, information on the individual method tests.)

        This functionallity is not currently used (and not functional on the
        University system as of 8-13), and may need to be re-interfaced.
        """
        
        reportfile=file(self.reportpath,'a')
        reportfile.write('\n<FUNCTIONTEST func="%s" >' %(funcName))
        for line in errorList:
            reportfile.write('\n%s' %(line))
        
        reportfile.write('\n</FUNCTIONTEST>')
        reportfile.close()

        
    def completeReport(self):
        """
        When we're done writing to the Tarsqi test report, we need to be able
        to put a /TARSQITEST tag at the end of it to make it a valid xml file.
        Any other final bookkeeping should be done here. This step is to be
        perfomed immediately before the log file gets written, so at this stage
        any report file must be readable by the regression tester.
        """
        # Open the report file and append the closing tag to it.
        reportfile=file(self.reportpath,'a')
        reportfile.write('\n</TARSQITEST>')
        reportfile.close()


        
if __name__ == '__main__':


    if len(sys.argv) > 3:
        
        mode = sys.argv[1]
        if mode == 'create':
            create_suites(sys.argv[2],sys.argv[3])
        elif mode == 'run':
            buildSuite(sys.argv[2],sys.argv[3])

    else:
        
        print "\nUsage:\n"
        print "   % ttk_test.py create <definition_file> <directory>"
        print "   % ttk_test.py run <MOD_LIST|'all'|'none'> <TYPE_LIST|'all'>\n"

        

"""
For each module that ttk_test is told to test, it creates a ModuleTest Object.
Each ModuleTest needs to be given the name of the module it's testing, the
filetypes it is to test, and the name of the file where it is to find all
of its test cases.
"""



from unittest import TestCase
from unittest import TestSuite
from base_case import base_case
from os import path
from os import mkdir
from test_results import module_result
from ttk_path import TTK_ROOT



class ModuleTest(TestCase):

    """
    A ModuleTest a collection of smaller test cases, each of which
    is a BaseCase object, that all get run when the ModuleTest is run. A
    ModuleTest is essentially a TestSuite object pretending to be a TestCase
    object. 

    Instance Variables:
        types - string: comma separated list of file types to test
        filelist - string: name of the file that stores the test cases
        module - string: name of the module that is being tested. Used to
                         navigate directory structure, and is passed to
                         BaseCase objects
        module_suite - TestSuite:  Contains all the BaseCase objects
        result - module_result: the TestResult object associated with the
                                TestSuite that this ModuleTest runs.
        timestamp - string: used as a directory name to store files showing
                              where failures occured
                                
    """

    types=None
    timestamp = None
    filelist='filelist.txt'
    module=None
    ACCEPTED_FILETYPES=['simple-xml','timebank','rte3']
    

    
    def setUp(self):

        """
        Before the ModuleTest is run, we build the TestSuite of BaseCases that
        are needed.
        """

        # Instantiate a TestSuite object:
        self.module_suite=TestSuite()
        # Open up the filelist file and read it into memory:
        namesfile=open(path.join(TTK_ROOT,'testing_new','suites',self.module,self.filelist))
        rawtext=namesfile.read()
        namesfile.close()
        # Start a list of BaseCases:
        test_cases=[]
        filetypes=[]
        if self.types=='all':
            filetypes=self.ACCEPTED_FILETYPES
        else:
            filetypes=self.types.split(',')

        for ftype in filetypes:

            if ftype in self.ACCEPTED_FILETYPES:

                # Find the place in the file list that lists that file type:
                
                lookfortag='%s>' %(ftype.upper())
                start=rawtext.find('<%s' %lookfortag)
                end=rawtext.find('</%s' %lookfortag)
                counter=rawtext.find("<",start+1)
                # Start a list of file names:
                filenames=[]

                # For each file listed in this section of the file list:
                while counter < end:
                    # Find the place in the enrty that contains the name of the file
                    nameStart=rawtext.find("'",rawtext.find("name",counter))
                    # Record the filename:
                    filename=rawtext[nameStart+1:rawtext.find("'",nameStart+1)]
                    # Find the comment and store it:
                    commentStart=rawtext.find("'",rawtext.find("comment",counter))
                    comment=rawtext[commentStart+1:rawtext.find("'",commentStart+1)]
                    # Append to the list of file names a tuple containing this
                    # filename and this comment:
                    filenames.append((filename,comment))
                    counter=rawtext.find("<",counter+1)

                #for item in filenames:
                for (filename, comment) in filenames:
                    # Instantiate a new BaseCase and give it the info it needs
                    case = base_case()
                    #print filename, ftype
                    case.filename = filename
                    case.comment = comment
                    case.filetype = ftype
                    case.module = self.module
                    case.timestamp = self.timestamp
                    # Add the BaseCase to the list of base cases:
                    test_cases.append(case)





       
        # Feed all of the BaseCases in the list into the TestSuite:
        self.module_suite.addTests(test_cases)
        # Create a ModuleResult object, telling it which module is being tested 
        self.result=module_result(self.module)

        # Create a directory in /testing_new/suites/<module>/reports to save
        # any failures that may occur in.
        dirpath=path.join(TTK_ROOT,'testing_new','suites',self.module,'reports',self.timestamp)
        mkdir(dirpath)

        
        

    def runTest(self):
        """
        When the ModuleTest is run, it runs all of the base cases in its test
        suite. If any of them result in failures or errors, then the ModuleTest
        signals a failure to the test suit that it is part of.
        """
        # Run this ModuleTest's test suite, using this test's ModuleReport:
        self.module_suite.run(self.result)
        # Call the end-of-test bookkeeping on the ModuleReport:
        self.result.completeReport()
        # If the ModuleReport contains no failures and no errors, then end
        # in success
        if len(self.result.failures)==len(self.result.errors)==0:
            return
        # Otherwise, end in failure:
        else:
            self.fail('failures / errors on module %s') %(self.module)


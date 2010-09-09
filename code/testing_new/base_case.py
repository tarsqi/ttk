"""
A BaseCase (base_case) object is the smallest level of testing in the component
tests. Each BaseCase has a single .xml file that it runs through some Tarsqi
component and another .xml file to which it compares the output from that run.
"""

# Modified 7/22/08 -kt

import unittest
import compare_xml
import tarsqi
import os
from ttk_path import TTK_ROOT





class base_case(unittest.TestCase):
    """
    A BaseCase object is told the name of the file it is working with, the
    module (component) it is working on, and the type of the input file (rte3,
    timebank,simple-xml), and it is also handed the string TTK_PATH

    Instance variables:
        filename - string

        filetype - string
        module - string
        comment -string
        changes - list of 8-tuples
        in_string - string  .
        ob_string - string   . The input and observed and expected output,
        ex_string - string  .         as strings
        removeme - string: Path to the file created by Tarsqi, which must be
                            deleted after the test is run
        timestamp - string: used as a directory name to store files showing
                              where failures occured
    """

    filename = None
    filetype= None
    module = None
    comment = ''
    timestamp = None
    changes=[]


    def setUp(self):
        """
        Before the test is run, opens up the files for the input and expected
        output, stores them as strings, runs the correct component on the input
        and stores the observed output as a string:
        """
        # Using TTK_ROOT, the module name, and the file name, work out the
        # paths to the two files we need:
        filespath = os.path.join(TTK_ROOT,'testing_new','suites',self.module,self.filetype)
        inputpath = os.path.join(filespath,'input',self.filename)
        exoutpath = os.path.join(filespath,'expected_out',self.filename)
        # Work out the path to give Tarsqi for its output file, then store that
        # path to delete it later:
        oboutpath = os.path.join(filespath,self.filename)
        self.removeme=oboutpath
        # Use the module name to create the pipeline argument to feed to Tarsqi:
        pipeline = "pipeline="+self.module.upper()
        # Run Tarsqi on the input file. Set "trap errors" to false so that
        # errors that Tarsqi generates will be propagated up:
        tarsqi.run_tarsqi([self.filetype,pipeline,'trap_errors=False',inputpath,oboutpath])
        # Store the contents of input file, the observed output file, and the
        # expected output file as strings:
        self.in_string=self.unpack(inputpath)
        self.ex_string=self.unpack(exoutpath)
        self.ob_string=self.unpack(oboutpath)
        
        
    def NEWsetUp(self):
        """
        Before the test is run, opens up the files for the input and expected
        output, stores them as strings, runs the correct component on the input
        and stores the observed output as a string:
        """
        # Using TTK_ROOT, the module name, and the file name, work out the
        # paths to the two files we need:
        filespath = os.path.join(TTK_ROOT,'testing_new','suites',self.module,self.filetype)
        inputpath = os.path.join(filespath,'input',self.filename)
        exoutpath = os.path.join(filespath,'expected_out',self.filename)
        # Work out the path to give Tarsqi for its output file, then store that
        # path to delete it later:
        oboutpath = os.path.join(filespath,self.filename)
        self.removeme=oboutpath
        # Use the module name to create the pipeline argument to feed to Tarsqi:
        pipeline = "pipeline="+self.module.upper()
        # Run Tarsqi on the input file. Set "trap errors" to false so that
        # errors that Tarsqi generates will be propagated up:
        print 'ole'
        tarsqi.run_tarsqi(['simple-xml',pipeline,'trap_errors=False',inputpath,oboutpath])
        # Store the contents of input file, the observed output file, and the
        # expected output file as strings:
        self.in_string=self.unpack(inputpath)
        self.ex_string=self.unpack(exoutpath)
        self.ob_string=self.unpack(oboutpath)
        
        
    def runTest(self):
        """
        When the test is run, use compare_xml.py to compare the observed output
        to the expected output. This returns a list of discrepencies. If this
        list is non-empty, BaseCase reports a failure.
        """
        # Call compare_xml with the expected and observed strings as arguments.
        # Store the list it returns in self.changes:
        self.changes = compare_xml.comp(self.ex_string,self.ob_string)
        # If compare_xml indicates differences between the two files, indicate
        # a failure. Otherwise end in success
        if self.changes[1] or self.changes[3]:
            self.fail(self.module + ' file:  ' + self.filename + "    ")

    def unpack(self,filename):
        """
        Auxilliary method to read the contents of a file into a string.

        Arguments:
            filename - string

        Returns:
            a string, the contents of the file named 'filename'
        """
        file1=open(filename)
        text=file1.read()
        file1.close
        return text


    def tearDown(self):
        """
        After the test is run, removes the file that Tarsqi created for its
        output. If the file is not destroyed, then Tarsqi will call an error
        next time the test is run.
        """
        os.remove(self.removeme)
        

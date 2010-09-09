"""
Each ModuleTest uses a module_result object to keep track of what test cases
passed and failed, and to write that information into the module report file.

It is important to note that the module_result object is the TestResult object
that is reported to by the TestSuite _contained_inside_ the ModuleTest object.
Therefore, the failures and errors that this module_result class responds to
are those reported by BaseCase objects.
The ModuleTest itself reports to a TarsqiResult object instead.
"""
# Modified 8/20/08  -kt

from unittest import TestResult
from datetime import datetime
from os import path
from ttk_path import TTK_ROOT




def reformat(string,replace_newlines=True):
    """
    This is a utility method that takes the pieces of TimeML text that are
    passed along as failures and replaces angle brackets with double square
    brackets so that they do not interfere with the xml format of the report
    file.
    """
    # Helper method so that snippets of XML can be included in the report file
    # (which is also XML) without creating problems. This method simply goes
    # through a string and replaces all '<'s and '>'s with '[' and ']', and
    # also replaces any newlines (\n) with '{CR}'
    newstring=string.replace('<','[').replace('>',']')
    if replace_newlines == True:
        newstring=newstring.replace('\n','<br>')
    return newstring





class module_result(TestResult):
    """
    A module_result (ModuleResult) object writes the module report file based
    on the outcomes of individual BaseCases.

    Instance Variables:
        failures - list of failures
        errors - list of errors
        testsRun - int
        shouldStop - int (unittest internal. unused here)
        module - string
        reportname - string: the name of the report file for this module report
        reportpath - string: the full path to the report file
    """

    def __init__(self,module):
        """
        Sets up the object and writes the header of the report file.

        Arguments:

            module - string: the module being tested.
        """
        # from superclass init method:
        self.failures = []
        self.errors = []
        self.testsRun = 0
        self.shouldStop = 0
        ##


        self.module=module
        # Create the correct path to the file the module report will be stored:
        self.reportname="%sreport.txt" %module
        self.reportpath=path.join(TTK_ROOT,'testing_new','suites',self.module,\
                                'reports',self.reportname)
        # Open the report file and write the opening header:
        reportfile=file(self.reportpath,'w')
        headertext = "<TEST module='%s'>\n" %(self.module)
        reportfile.write(headertext)
        reportfile.close()

    def startTest(self,test):
        """
        Before each test is run, inserts the neccesary test file information
        into the report.

        Arguments:
            test - BaseCase: the test that is about to be run.
        """
        # Increment a counter:
        self.testsRun+=1
        # Create the proper header tag for the test file that is about to be run
        # and write it into the report file:
        newtext="<FILE filename='%s' filetype='%s' comment='%s' " %(test.filename,test.filetype,test.comment)
        reportfile=file(self.reportpath,'a')
        reportfile.write(newtext)
        reportfile.close()

        
        

    def addError(self,test,err):
        """
        When a test case indicates an error, writes the appropriate data into
        the test report

        Arguments:
            test - BaseCase
            err - 3-tuple (unittest internal error reporting style)
        """
        
        # Retrieve the name of the file that the error occured on:
        filename=test.filename
        # Create the proper text for the report:
        newtext="failures='0' errors='1'>\n<ERROR>%s</ERROR>\n</FILE>\n\n" %(err[1])
        # Write the text to the report file:
        reportfile=file(self.reportpath,'a')
        reportfile.write(newtext)
        reportfile.close()
        # Add the error to the error list (used as a counter)
        self.errors.append((test,err))
        
    

    def addFailure(self,test,err):
        """
        When the test case indicates a failure, writes the proper data into the
        test report

        Arguments:
            test - BaseCase
            err - 3-Tuple (unittest internal)
        """
        
        # Record the name of the file that caused failures:
        filename=test.filename
        # Retrieve the lists that represents the differences between expected
        # and observed output
        failings=test.changes

        # Determine the path to the file where the expected and observed out-
        # puts will be stored:
        failfilename='%s.%s'%(test.filetype,test.filename)
        failfilepath=path.join(TTK_ROOT,'testing_new','suites',test.module,'reports',test.timestamp,failfilename)


        
        # Begin the text that will be appended to the report by closing the
        # header tag, noting the number of failures:
        numfails=len(failings[1])+len(failings[3])
        newtext="failures='%i' errors='0'>\n" %(numfails)
        
        # For each line in the list of failures, create a line of xml to put
        # into the report that gives the neccesary details about the failure,
        # and append it to the text begun above:
        self.failures.append((test,failings)) # This is needed so the TarsqiTest
                                              # object knows a failure has
                                              # occured
        #    newtext+="<FAILURE "
            #if line[0]=='insert':
            #    newtext+="errorType='insert' object='[[%s]]'> %s </FAILURE>\n" %(reformat(line[1]),reformat(line[7]))
            #elif line[0]=='omit':
            #    newtext+="errorType='omit' object='[[%s]]'> %s </FAILURE>\n" %(reformat(line[1]),reformat(line[4]))
            #elif line[0]=='mismatch':
            #    newtext+="errorType='mismatch' object='%s'> <EXPECTED>%s</EXPECTED> <OBSERVED>%s</OBSERVED> </FAILURE>\n"%(line[1],reformat(line[4]),reformat(line[7]))
            #else:
            #    newtext+="errorType='unknown' expected='%s' observed='%s'></FAILURE>\n" \
            #              %(reformat(line[4]),reformat(line[7]))
        # Include the path to the file where the expected and observed texts are stored:
        newtext+="<FAILURE path='%s'/>" %failfilepath        


        newtext+="</FILE>\n\n"

        # Now append the text to the report file:
        
        reportfile=file(self.reportpath,'a')
        reportfile.write(newtext)
        reportfile.close()

        ## Store a copy of the output file, annotated with failure info,
        ## in the reports directory:

        # The value of 'failings' (which is the data tored in test.changes)
        # is a four element list. The 0th element is the list of xml components
        # of the expected output (as determined by the xml parser), the 1st
        # element is a list of the indexes of the components that do not exist
        # in the observed output. The 2nd and 3rd elements are the complement
        # for the observed output: a list of compenents, and a list of indexes
        # of unmatched components.

        exp,experr,obs,obserr=failings


        annotatedtext=u'<TTKTestFailure><Expected>'

        for i in range(len(exp)):
            if i in experr:
                if exp[i].is_tag():
                    if exp[i].content[1] != '/':
                        if exp[i].attrs.has_key(u'class'):
                            exp[i].attrs[u'eclass']=exp[i].attrs[u'class']
                        exp[i].attrs[u'class']=u'MissedTag'
                        new_cont=u'<%s'%(exp[i].get_tag())
                        for key in exp[i].attrs.keys():
                            new_cont += u' %s="%s"'%(key,exp[i].attrs[key])
                        new_cont+=u'>'
                        annotatedtext+=new_cont
                    else:
                        annotatedtext+=exp[i].content
                else:
                    annotatedtext+=exp[i].content
# Is something like this needed?:
#                else:
#                annotatedtext+=u'<MissedText>'+exp[i]+u'</MissedText>'
            else:
                annotatedtext+=exp[i].content

        annotatedtext += u'</Expected><Observed>'

        for i in range(len(obs)):
            if i in obserr:
                if obs[i].is_tag():
                    if obs[i].content[1] != '/':
                        if obs[i].attrs.has_key(u'class'):
                            obs[i].attrs[u'eclass']=obs[i].attrs[u'class']
                        obs[i].attrs[u'class']=u'AddedTag'
                        new_cont=u'<%s'%(obs[i].get_tag())
                        for key in obs[i].attrs.keys():
                            new_cont += u' %s="%s"'%(key,obs[i].attrs[key])
                        new_cont+=u'>'
                        annotatedtext+=new_cont
                    else:
                        annotatedtext+=obs[i].content
                else:
                    annotatedtext+=obs[i].content
            else:
                annotatedtext+=obs[i].content

        annotatedtext += u'</Observed></TTKTestFailure>'
        
 
        
        


        # Open the file in the reports directory, write the annotated text to
        # it, and close the file:
        
        failfile=open(failfilepath,'w')
        
        failfile.write(annotatedtext)
        failfile.close()
        
        

    def addSuccess(self,test):
        """
        After a test completes sucessfully, complete the entry for this test:

        Arguments:
            test - BaseCase
        """

        # create the text neccesary, indicating success:
        newtext="failures='0' errors='0'>\n</FILE>\n\n"
        # Write the text to the report file:
        reportfile=file(self.reportpath,'a')
        reportfile.write(newtext)
        reportfile.close()

        


    def completeReport(self):
        """
        After all tests have been run, this method must run to write the closing
        tag in the report file.
        """
        # Open the report file and write the closing tag onto it.
        reportfile=file(self.reportpath,'a')
        reportfile.write("</TEST>")
        reportfile.close()

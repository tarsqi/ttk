"""
Regress.py is the regression testing module for TARSQI. It examines the /testing
/logfile.txt file and the tarqsitest reports in testing/reports/ and produces
a report showing how each individual testcase has performed over time.

USAGE

    Currently, regress.py is run from the command line with no arguments. It
    examines the report files and writes its results in a file /testing/reports/
    table.html
    

"""

from ttk_path import TTK_ROOT
import ttk_test
from os import path


class RegressionTester:
    """
    Instance Variables:
        TestList - list of (string,string) pairs
                    (names of report files and dates created)
        FilesDir - dictionary of dictionaries of strings
                    (index of all known test files, by module and filetype)
    """

    def __init__(self):
        """
        A RegressionTester object contains a list of all tarsqitest report files
        that it has found, as well as a list of all individual testcases that
        were run in any of those tarsqitests, indexed by module and filetype.
        When the init method is run, /testing/logfile.txt is examined, and
        for each entry in the logfile, the report file located in /testing
        /reports/ is examined, and each testcase file that was recorded in the
        report is added to the list of testcases.
        """
        # Initialize a list of names of TarsqiTest report files:
        self.TestList=[]
        # From testing/logfile.txt, read the report names from disk and store
        # them in TestList:
        logfile=file(path.join(TTK_ROOT,'testing','logfile.txt'),'r')
        line=logfile.readline()
        while line.startswith('<TARSQITEST'):
            # For each entry in logfile.txt, add to TestList a tuple containing
            # the name of the report file and the date it was run:
            namestart=line.find("'",line.find("location"))
            name=line[namestart+1:line.find("'",namestart+1)]
            datestart=line.find("'",line.find("date"))
            date=line[datestart+1:line.find("'",datestart+1)]
            self.TestList.append((name,date))
            line=logfile.readline()
        logfile.close()

        
        
        # Initialize the structure of FilesDir:
        self.FilesDir={}
        for modname in ['gutime','evita','slinket','s2t','blinker']:
            subDir={}
            for filetype in ['simple-xml','timebank','rte3']:
                subDir[filetype]=set([])
            self.FilesDir[modname]=subDir
        

        
        
        ## Open each report file, one at a time. For each one, run through it
        ## a line at a time, and for each <FILE ...> tag encountered, place
        ## that file's name in the appropriate bin of self.FilesDir:
        
        for item in self.TestList:
            reportFileName=item[0]
            # Open the report file and read the first line:
            reportFile=file(path.join(TTK_ROOT,'testing','reports',reportFileName),'r')
            line=reportFile.readline()
            # While the current line is not the end of the file:
            moduleName=''
            while not(line.startswith('</TARSQITEST')):
                # Each time a "TEST" tag is encountered, it indicates a new
                # module is being tested:
                if line.startswith('<TEST'):
                    stName=line.find("'",line.find("module="))
                    moduleName=line[stName+1:line.find("'",stName+1)]
                # Each "FILE" tag indicates a single testcase
                if line.startswith('<FILE'):
                    stFName=line.find("'",line.find("filename="))
                    fileName=line[stFName+1:line.find("'",stFName+1)]
                    stType=line.find("'",line.find("filetype="))
                    fileType=line[stType+1:line.find("'",stType+1)]
                    self.FilesDir[moduleName][fileType].add(fileName)
                line=reportFile.readline()
            reportFile.close()

        



    def make_filelist(self,modules,filetypes):
        """
        The method make_filelist allows the user to examine a subset of the
        entire list of test cases that have ever been run. The arguments are
        lists of strings representing which modules and which filetypes the
        user wishes to examine, and the output is a list of 3-tuples that
        will be recognized by the method compile_info().

        ARGUMENTS
            modules - list of strings (the modules that the user wants to see
                                        the results for)
            filetypes - list of strings (the file types the user wants to see
                                        the results for)
        """
        filelist=[]
        # For each pairing of module name and file type, look in the appropriate
        # "drawer" in the FilesDir dictionary and append each filename contained
        # there to the file list:
        for module in modules:
            for filetype in filetypes:
                for filename in self.FilesDir[module][filetype]:
                    filelist.append((module,filetype,filename))
        return filelist
                    

    def compile_info(self,reportslist,filelist):
        """
        The compile_info() method does the work of examining each report file
        and determining the outcome of each test case that is to be examined
        (either pass, fail, error, or test not run). The outcomes are recorded
        in a 2-dimensional array, with each cell conatining a tuple consising
        of the result of the test and the comment that was recorded at the time
        the test was run

        ARGUMENTS
            reportslist
        """
        passFailArray=[]
        for filetuple in filelist:
            module,filetype,filename=filetuple
            fileEntry=[]
            for reportfilename in reportslist:
                reportfile=file(reportfilename,'r')
                line=reportfile.readline()
                
                while not(line.startswith('</TARSQITEST')):
                    
                    if line.startswith("<TEST module='%s'"%module):
                        break
                    line=reportfile.readline()
                if line.startswith('</TARSQITEST'):
                    fileEntry.append(('NO TEST',''))
                    continue
                else:
                    line=reportfile.readline()
                    while not(line.startswith("</TEST")):
                        if not(line.startswith("<FILE")):
                            line=reportfile.readline()
                            continue
                        stFName=line.find("'",line.find("filename="))
                        fName=line[stFName+1:line.find("'",stFName+1)]
                        stFType=line.find("'",line.find("filetype="))
                        fType=line[stFType+1:line.find("'",stFType+1)]
                        if fName==filename and fType==filetype:
                            failures=getAttr(line,'failures')
                            errors=getAttr(line,'errors')
                            comment=getAttr(line,'comment')
                            if failures != '0':
                                fileEntry.append(('FAIL',comment))
                            elif errors != '0':
                                fileEntry.append(('ERROR',comment))
                            else:
                                fileEntry.append(('PASS',comment))                                
                            break
                        else:
                            line=reportfile.readline()
                            continue
                    if line.startswith("</TEST"):
                        fileEntry.append(("NO TEST",""))
            reportfile.close()
            passFailArray.append(fileEntry)
        return passFailArray

    def displayresults(self,reportslist,filelist):
        
        array=self.compile_info(reportslist,filelist)

        text=file(path.join(TTK_ROOT,'testing','reports','table.html'),'w')

        text.write('<html>\n<body>\n<table border="3">\n<th>File \ Test</th>\n')
        for name in reportslist:
            justname=name.split(path.sep)[-1]
            withoutext=justname.split('.')[0]
            text.write('<th>%s</th>' %withoutext)
        for i in range(len(filelist)):
            text.write('<tr>\n<td>%s.%s.%s</td>\n'%(filelist[i][0],filelist[i][1],filelist[i][2]))
            for j in range(len(reportslist)):
                outcome=array[i][j][0]
                comment=array[i][j][1]
                color='black'
                if outcome=='PASS':
                    color='green'
                if outcome=='FAIL':
                    color='red'
                    reportpathname=reportslist[j][:-4].split(path.sep)[-1]
                    # print reportpathname
                    pathtobadfile=path.join(TTK_ROOT,'testing','test_suite',filelist[i][0],'reports',reportpathname,'%s.%s'%(filelist[i][1],filelist[i][2]))
                    outcome='<a href="%s"><font color="red">FAIL</font></a>'%pathtobadfile
                if outcome=='ERROR':
                    color='#C0C000'
                text.write('<td><font color="%s"><center>%s<br/>%s</center></font></td>'%(color,outcome,comment))
        
        

            text.write('</tr>\n')

        text.write('</table>\n</body>\n</html>')
        text.close()
        
        
                
                        
                        
                  
                    
                

     



def getAttr(line,attrib):
    """
    Helper method to pull out the value of a given attribute from a line of XML.
    """
    stVal=line.find("'",line.find('%s='%attrib))
    val=line[stVal+1:line.find("'",stVal+1)]
    return val




if __name__ == '__main__':
    regress=RegressionTester()

    reportlist=[]
    for item in regress.TestList:
        reportlist.append(item[0])
    filelist=regress.make_filelist(['gutime','evita','slinket','s2t','blinker'],['simple-xml','timebank','rte3'])
    
    regress.displayresults(reportlist,filelist)    

    
        
    

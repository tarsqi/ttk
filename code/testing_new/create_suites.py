"""

Takes the contents of test_suites.xml and creates data that can be
easily added to the suites of all components. Takes the current
version of the toolkit and create intermediate processing versions of
all test cases in the suite.

Usage 1:

   python test_suites.py file base_dir

Usage 2:

   file = 'test_suites.xml'
   base_dir = 'tmp'
   from test_suites import create_suites
   create_suites(file, base_dir)

The input file contains suites using the following syntax:

   <SUITES>

   <SUITE 
      name='basic-regression-1' 
      comment='Initial cases used for regression'>

      <case name='01.xml' comment=''>
      Mr. Vinken is Vinken Jr. Or is he senior?
      </case>

      <case name='02.xml' comment='hopsa'>
      He saw an explosion.
      </case>

      <case name='03.xml' comment=''>
      He forgot to sleep.
      </case>

      <case name='04.xml' comment=''>
      Prof. Jones is waiting for his wedding.
      </case>

   </SUITE>

   </SUITES>

The cases are written as files to base_dir/suite_name, with versions
for all stages of processing using the current toolkit. In addition, a
file named files.txt is created for each suite. The suites can be
moved manually to the suites directory, the contents of file.txt
should be added to the file filelist.txt that comes with every suite.

The directory base_dir is assumed to be empty.

"""

import sys, os, time
import xml.dom.minidom
import tarsqi


def run_tarsqi(module, case_name, dir_in, dir_out):

    options = {'trap_errors': 'False', 'pipeline': module}
    infile = "%s/%s" % (dir_in, case_name)
    outfile = "%s/%s" % (dir_out, case_name)
    tarsqi.Tarsqi('simple-xml', options, infile, outfile).process()
    

def create_suites(file, base_dir):

    dom = xml.dom.minidom.parse(file)
    now = time.strftime("%Y/%m/%d %H:%M:%S %Z")

    for suite in dom.documentElement.getElementsByTagName('SUITE'):
    
        print "\n<SUITE name=\"%s\">\n" % suite.getAttribute('name')

        suite_name = suite.getAttribute('name')
        suite_comment = suite.getAttribute('comment')
        dir = os.path.join(base_dir, suite_name)
        dir_in =  os.path.join(base_dir, suite_name, '1-in')
        dir_pre =  os.path.join(base_dir, suite_name, '2-pre')
        dir_gut =  os.path.join(base_dir, suite_name, '3-gut')
        dir_evi =  os.path.join(base_dir, suite_name, '4-evi')
        dir_sli =  os.path.join(base_dir, suite_name, '5-sli')
        dir_s2t =  os.path.join(base_dir, suite_name, '6-s2t')
        dir_bli =  os.path.join(base_dir, suite_name, '7-bli')
        dir_cla =  os.path.join(base_dir, suite_name, '8-cla')
        for d in [dir, dir_in, dir_pre, dir_gut, dir_evi, dir_sli,
                  dir_s2t, dir_bli, dir_cla]:
            os.mkdir(d)

        filelist = open(os.path.join(dir, 'files.txt'), 'w')
        filelist.write("<%s created=\"%s\" comment=\"%s\">\n" % \
                       (suite_name, now, suite_comment))

        for case in suite.getElementsByTagName('case'):
            case_name = case.getAttribute('name')
            case_comment = case.getAttribute('comment')
            case_content = ''.join([node.data for node in case.childNodes])
            filelist.write("<FILE name=\"%s\" comment=\"%s\">\n" % (case_name, case_comment))
            case_file = open( os.path.join(dir_in, case_name), 'w')
            case_file.write('<TEXT>' + case_content + '</TEXT>')
            case_file.close()
            run_tarsqi('PREPROCESSOR', case_name, dir_in, dir_pre)
            run_tarsqi('GUTIME', case_name, dir_pre, dir_gut)
            run_tarsqi('EVITA', case_name, dir_gut, dir_evi)
            run_tarsqi('SLINKET', case_name, dir_evi, dir_sli)
            run_tarsqi('S2T', case_name, dir_sli, dir_s2t)
            run_tarsqi('BLINKER', case_name, dir_evi, dir_bli)
            run_tarsqi('CLASSIFIER', case_name, dir_evi, dir_cla)

        filelist.write("</%s>\n" % suite_name)

    dom.unlink()
    
            
if __name__ == '__main__':

    (file, base_dir) = sys.argv[1:3]
    create_suites(file, base_dir)


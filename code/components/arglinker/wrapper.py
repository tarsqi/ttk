"""

Contains the ArgLinker wrapper.

"""

import os, os.path

from ttk_path import TTK_ROOT

from library.tarsqi_constants import ARGLINKER
from components.arglinker.main import ArgLinker

from docmodel.xml_parser import Parser
from utilities.converter import FragmentConverter


# set this one to True if we want to use the simplistic Python version
USE_SIMPLE_LINKER = False
#USE_SIMPLE_LINKER = True


class ArgLinkerWrapper:

    """Wrapper for ArgLinker."""


    def __init__(self, tag, xmldoc, tarsqi_instance):
        """Calls __init__ of the base class and sets component_name, parser, CREATION_EXTENSION
        and RETRIEVAL_EXTENSION."""
        self.component_name = ARGLINKER
        self.parser = ArgLinker()
        self.CREATION_EXTENSION = 'arg.i.xml'
        self.TMP1_EXTENSION = 'arg.t1.xml'
        self.TMP2_EXTENSION = 'arg.t2.xml'
        self.RETRIEVAL_EXTENSION = 'arg.o.xml'

    def process_fragments(self):
        """Apply the Slinket parser to each fragment. No arguments and no return value."""
        for fragment in self.fragments:
            base = fragment[0]
            infile = "%s%s%s.%s" % \
                     (self.DIR_DATA, os.sep, base, self.CREATION_EXTENSION)
            tmp1file = "%s%s%s.%s" % \
                      (self.DIR_DATA, os.sep, base, self.TMP1_EXTENSION)
            tmp2file = "%s%s%s.%s" % \
                      (self.DIR_DATA, os.sep, base, self.TMP2_EXTENSION)
            outfile = "%s%s%s.%s" % \
                      (self.DIR_DATA, os.sep, base, self.RETRIEVAL_EXTENSION)
            if USE_SIMPLE_LINKER:
                self.parser.process(infile, outfile)
            else:
                # prepare input to arglinker
                self.xmldoc = Parser().parse_file(open(infile,'r'))
                self.create_arglinker_input(tmp1file)
                # run shell command to set the arglinker to work, for
                # now it just copies the example file to the output of
                # the arglinker
                #os.system("cp %s %s" % (TTK_ROOT + os.sep + 'wsj_0001.mrg.dep.pos', tmp2file))
                dp_prog = os.path.join(TTK_ROOT, 'utilities', 'depParser', 'depParse-wrapper')
                dp_input = tmp1file
                dp_output = tmp2file
                dp_model = os.path.join(TTK_ROOT, 'utilities', 'depParser', 'base.vp3.model')
                os.system("%s %s %s %s" % (dp_prog, dp_input, dp_output, dp_model) )
                self.parser.process(infile, outfile, dp_output)
                #os.system('/home/j/llc/wellner/depParser/depParseDecode.native -input /home/j/llc/wellner/depParser/ex-data/ -output <some output directory> -out-suffix ".DEP" -model /home/j/llc/wellner/depParser/base.vp3.model')
                # retrieve result - this is done in main.py
            

    def create_arglinker_input(self, tmp1file):
        """Take the xmldoc variable and create the input needed for the arglinker."""
        fh = open(tmp1file,'w')
        fh.write("<DOC>\n")
        for element in self.xmldoc.elements:
            if element.is_opening_tag():
                if element.tag == 's':
                    fh.write("<sentence>\n")
                    fh.write("<tokens>\n")
                elif element.tag == 'lex':
                    fh.write(element.content)
            elif element.is_closing_tag():
                if element.tag == 's':
                    fh.write("</tokens>\n")        
                    fh.write("<dep_parse>\n")
                    fh.write("</dep_parse>\n")
                    fh.write("</sentence>\n")
                elif element.tag == 'lex':
                    fh.write(element.content)
            else:
                fh.write(element.content)
        fh.write("</DOC>\n")


    def import_arglinker_output(self, tmp2file, outfile):

        """Takes a file with the results of the dependency parse (tmp2file), finds the arguments
        in there, adds them to the xmldoc, and saves the xmldoc (to outfile)."""
    
        # this is how to get the shallow tree, probably of limited use because the
        # dep_parse will not be part of the tree
        doctree = FragmentConverter(self.xmldoc, tmp2file).convert(user=ARGLINKER)
        doctree.pretty_print()
        
        # code to deal with the contents of dep_parse, link the ids there to the lexids
        # and to create a list of arglinks (this could even be more general, creating a
        # list of all dependencies, but subtyping some of them as arglinks)

        # supposing we have a list of arglinks, here we add them to the xmldoc

        # finally, save the updated xmldoc
        self.xmldoc.save_to_file(outfile)

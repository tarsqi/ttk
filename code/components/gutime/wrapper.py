"""Contains the GUTime wrapper.

The wrapper takes the content of all TarsqiDocElements in the TarsqiDocument and
creates the input needed by TimeTag.pl, which is the wrapper around TempEx.pm.

The input required by TimeTag.pl looks as follows:

   <DOC>
   <DATE>20120912</DATE>
   <s>
      <lex id=1 pos="NNP">Monday</lex>
      <lex id=2 pos="NN">morning</lex>
      <lex id=3>and</lex>
      <lex id=4>today</lex>
   </s>
   </DOC>

The DOC root is required and so is the DATE tag. Otherwise, only s and lex tags
are allowed. Any kind of spacing between the tags is allowed.

Note that the directory that this wrapper is in has two unused files: gutime.pl
and postTempEx.pl. Much of the functionality in those files is either in this
wrapper or obsolete. They are kept around for reference.

"""

import os, subprocess, codecs
from xml.dom.minidom import parse

from library.tarsqi_constants import GUTIME
from utilities import logger

TTK_ROOT = os.environ['TTK_ROOT']


class GUTimeWrapper:
    
    """Wrapper for GUTime."""

    def __init__(self, document):
        self.document = document
        self.component_name = GUTIME
        self.DIR_GUTIME = os.path.join(TTK_ROOT, 'components', 'gutime')
        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')

    def process(self):
        """Create the input required by TimeTag.pl, call the Perl script and collect the
        TIMEX3 tags."""
        os.chdir(self.DIR_GUTIME)
        count = 0
        for element in self.document.elements:
            count += 1
            fin = os.path.join(self.DIR_DATA, "doc-element-%03d.gut.in.xml" % count)
            fout = os.path.join(self.DIR_DATA, "doc-element-%03d.gut.out.xml" % count)
            _create_gutime_input(element, fin)
            _run_gutime(fin, fout)
            _import_timex_tags(fout, element)


def _create_gutime_input(element, fname):
    """Create input needed by GUTime (TimeTag.pl plus Tempex.pm)"""
    fh = codecs.open(fname, 'w', encoding='utf8')
    closing_s_needed = False
    fh.write("<DOC>\n")
    fh.write("<DATE>%s</DATE>\n" % element.doc.metadata.get('dct'))
    offsets = sorted(element.tarsqi_tags.opening_tags.keys())
    for offset in offsets:
        for tag in element.tarsqi_tags.opening_tags[offset]:
            if tag.name == 's':
                if closing_s_needed:
                    fh.write("</s>\n")
                fh.write("<s>\n")
                closing_s_needed = True
        for tag in element.tarsqi_tags.opening_tags[offset]:
            if tag.name == 'lex':
                text = element.doc.text(tag.begin, tag.end)
                fh.write("   %s\n" % tag.as_lex_xml_string(text))
    if closing_s_needed:
        fh.write("</s>\n")
    fh.write("</DOC>\n")

def _run_gutime(fin, fout):
    """Run the GUTIME Perls script."""
    command = "perl TimeTag.pl %s > %s" % (fin, fout)
    pipe = subprocess.PIPE
    p = subprocess.Popen(command, shell=True,
                         stdin=pipe, stdout=pipe, stderr=pipe, close_fds=True)
    (fh_in, fh_out, fh_errors) = (p.stdin, p.stdout, p.stderr)
    for line in fh_errors:
        logger.warn(line)

def _import_timex_tags(fname, element):
    """Take the TIMEX3 tags from the GUTime output and add them to the tarsqi
    tags dictionary."""
    dom = parse(fname)
    timexes = dom.getElementsByTagName('TIMEX3')
    for timex in timexes:
        lexes = timex.getElementsByTagName('lex')
        if lexes:
            p1 = int(lexes[0].getAttribute('begin'))
            p2 = int(lexes[-1].getAttribute('end'))
            timex_type = timex.getAttribute('TYPE')
            timex_value = timex.getAttribute('VAL')
            element.add_timex(p1, p2, timex_type, timex_value)

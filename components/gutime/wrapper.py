"""Contains the GUTime wrapper.

The wrapper takes all sentences in the TarsqiDocument and creates the input
needed by TimeTag.pl, which is the wrapper around TempEx.pm.

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
wrapper or obsolete. They are kept around for reference, mostly for the language
on temporal functions in postTempEx.pl.

"""

import os, sys, subprocess, codecs, StringIO
from xml.dom.minidom import parse, parseString

from components.preprocessing import chunker
from library.tarsqi_constants import GUTIME
from utilities import logger

TTK_ROOT = os.environ['TTK_ROOT']

# This variable determines whether GUTime is called using temporary files (the
# old way) or using an input string.
USE_TMP_FILES = False


class GUTimeWrapper:

    """Wrapper for GUTime."""

    def __init__(self, document):
        self.document = document
        self.component_name = GUTIME
        self.DIR_GUTIME = os.path.join(TTK_ROOT, 'components', 'gutime')
        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')

    def process(self):
        if USE_TMP_FILES:
            self.process_using_files()
        else:
            self.process_using_string()

    def process_using_files(self):
        """Create the input required by TimeTag.pl, call the Perl script and
        collect the TIMEX3 tags."""
        os.chdir(self.DIR_GUTIME)
        fin = os.path.join(self.DIR_DATA, "gut.in.xml")
        fout = os.path.join(self.DIR_DATA, "gut.out.xml")
        _create_gutime_input(self.document, fin)
        _run_gutime_on_file(fin, fout)
        dom = parse(fout)
        _export_timex_tags(self.document, dom)
        _update_chunks(self.document)

    def process_using_string(self):
        """Create the input required by TimeTag.pl, call the Perl script and
        collect the TIMEX3 tags."""
        os.chdir(self.DIR_GUTIME)
        string_buffer = _create_gutime_input(self.document)
        result = _run_gutime_on_string(string_buffer.getvalue())
        # apparently, parseString cannot deal with unicode
        # TODO: check whether this has unforeseen consequences
        result = u'{0}'.format(result).encode('utf-8')
        dom = parseString(result)
        _export_timex_tags(self.document, dom)
        _update_chunks(self.document)


def _create_gutime_input(tarsqidoc, fname=None):
    """Create input needed by GUTime (TimeTag.pl plus Tempex.pm). This method
    simply takes all sentences from the TarsqiDocument and relies on the
    existence of s tags and lex tags. If a file name is given than it will write
    the GUTime input to the file, if not, it will use a string buffer, write to
    it and then return it."""
    if fname is not None:
        fh = codecs.open(fname, 'w', encoding='utf8')
    else:
        fh = StringIO.StringIO()
    closing_s_needed = False
    fh.write("<DOC>\n")
    fh.write("<DATE>%s</DATE>\n" % tarsqidoc.metadata.get('dct'))
    offsets = sorted(tarsqidoc.tags.opening_tags.keys())
    for offset in offsets:
        for tag in tarsqidoc.tags.opening_tags[offset]:
            if tag.name == 's':
                if closing_s_needed:
                    fh.write("</s>\n")
                fh.write("<s>\n")
                closing_s_needed = True
            if tag.name == 'lex':
                text = tarsqidoc.sourcedoc.text[tag.begin:tag.end]
                fh.write("   %s\n" % tag.as_lex_xml_string(text))
    if closing_s_needed:
        fh.write("</s>\n")
    fh.write("</DOC>\n")
    return fh


def _run_gutime_on_string(input_string):
    """Run the GUTIME Perl script. This takes a string and returns a string."""
    command = ["perl", "TimeTag.pl"]
    pipe = subprocess.PIPE
    close_fds = False if sys.platform == 'win32' else True
    p = subprocess.Popen(command, stdin=pipe, stdout=pipe, stderr=pipe,
                         close_fds=close_fds)
    try:
        (result, error) = p.communicate(input_string)
        if error:
            logger.error(error)
        return result
    except UnicodeError:
        return input_string


def _run_gutime_on_file(fin, fout):
    """Run the GUTIME Perl script. Runs GUTime on an input file and creates an
    output file."""
    command = "perl TimeTag.pl %s > %s" % (fin, fout)
    pipe = subprocess.PIPE
    close_fds = False if sys.platform == 'win32' else True
    p = subprocess.Popen(command, shell=True,
                         stdin=pipe, stdout=pipe, stderr=pipe,
                         close_fds=close_fds)
    (fh_in, fh_out, fh_errors) = (p.stdin, p.stdout, p.stderr)
    for line in fh_errors:
        logger.warn(line)


def _export_timex_tags(tarsqidoc, dom):
    """Take the TIMEX3 tags from the GUTime output and add them to the tarsqi
    tags dictionary. The GUTime output is given as a DOM obect."""
    timexes = dom.getElementsByTagName('TIMEX3')
    for timex in timexes:
        lexes = timex.getElementsByTagName('lex')
        if lexes:
            p1 = int(lexes[0].getAttribute('begin'))
            p2 = int(lexes[-1].getAttribute('end'))
            attrs = {'tid': timex.getAttribute('tid'),
                     'type': timex.getAttribute('TYPE'),
                     'value': timex.getAttribute('VAL'),
                     'origin': GUTIME}
            tarsqidoc.add_timex(p1, p2, attrs)


def _update_chunks(tarsqi_document):
    """There are many cases where timexes do not fit into existing chunks, which
    means that they are ignored in later processing. We update the chunks to
    take this into account."""
    chunker.ChunkUpdater(tarsqi_document).update()

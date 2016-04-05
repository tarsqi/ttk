"""

Python wrapper around the merging code.

"""


USE_HERITAGE_CODE = True
USE_HERITAGE_CODE = False

import os, sys, subprocess

from library.tarsqi_constants import LINK_MERGER

if USE_HERITAGE_CODE:
    from library.timeMLspec import TLINK
    from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID
    from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, CONFIDENCE
    from utilities import logger
    #from docmodel.xml_parser import Parser
else:
    from components.merging.main import LinkMerger

TTK_ROOT = os.environ['TTK_ROOT']


class MergerWrapper:

    """Wraps the merging code, which includes Sputlinks temporal closure code."""


    def __init__(self, document):

        """Initialization depends on value of USE_HERITAGE_CODE. Initialize some or all of the
        following variables depending on the value: component_name, DIR_LINK_MERGER,
        CREATION_EXTENSION, TMP_EXTENSION and RETRIEVAL_EXTENSION."""

        self.component_name = LINK_MERGER
        self.document = document

        self.DIR_DATA = os.path.join(TTK_ROOT, 'data', 'tmp')
        self.CREATION_EXTENSION = 'mer.i.xml'
        self.RETRIEVAL_EXTENSION = 'mer.o.xml'
        if USE_HERITAGE_CODE:
            self.DIR_LINK_MERGER = os.path.join(TTK_ROOT, 'components', 'merging')
            self.TMP_EXTENSION = 'mer.t.xml'
        else:
            # using self.component here instead of self.parser, perhaps do the same for
            # the other components?
            self.component = LinkMerger()
            

    def process(self):
        self.process_fragments()

        
    def process_fragments(self):

        """Determines what version should run and then calls process_fragments_old or
        process_fragments_new."""

        if USE_HERITAGE_CODE:
            self.process_fragments_old()
        else:
            self.process_fragments_new()


    def process_fragments_new(self):

        """Set fragment names and ask the link merger component to process the fragments."""
        return
        for fragment in self.fragments:
            # set fragment names
            base = fragment[0]
            in_fragment = os.path.join(self.DIR_DATA, base+'.'+self.CREATION_EXTENSION)
            out_fragment = os.path.join(self.DIR_DATA, base+'.'+self.RETRIEVAL_EXTENSION)
            self.component.process(in_fragment, out_fragment)

            
    def process_fragments_old(self):

        """Set fragment names, call the perl merging script and insert the results back
        into the data."""

        os.chdir(self.DIR_LINK_MERGER + os.sep + 'sputlink')
        perl = self.document.getopt_perl()

        ## A fragment is a list with fragment name (fragment_001) and the first element of
        ## the xmldoc (the <TEXT> tag). The code relies on there being a file named
        ## fragment_001.mer.i.xml in the TMP directory. This file is an XML file with the
        ## <fragment> tag as a root, where this tag replaces the <TEXT> tag (not usre
        ## whether this replacement is essential).

        self.document.xmldoc.elements[0].tag = 'fragment'
        self.document.xmldoc.elements[-1].tag = 'fragment'
        self.fragments = [('fragment_001', self.document.xmldoc)]

        for fragment in self.fragments:
            # set fragment names
            base = fragment[0]
            in_fragment = os.path.join(self.DIR_DATA, base+'.'+self.CREATION_EXTENSION)
            tmp_fragment = os.path.join(self.DIR_DATA, base+'.'+self.TMP_EXTENSION)
            out_fragment = os.path.join(self.DIR_DATA, base+'.'+self.RETRIEVAL_EXTENSION)
            self.document.xmldoc.save_to_file(in_fragment)
            # process them
            command = "%s merge.pl %s %s" % (perl, in_fragment, tmp_fragment)

            pipe = subprocess.PIPE
            close_fds = False if sys.platform == 'win32' else True
            p = subprocess.Popen(command, shell=True,
                                 stdin=pipe, stdout=pipe, stderr=pipe, close_fds=clse_fds)
            (i, o, e) = (p.stdin, p.stdout, p.stderr)
            #(i, o, e) = os.popen3(command)
            for line in e:
                if line.lower().startswith('warn'):
                    logger.warn('MERGING: ' + line)
                else:
                    logger.error('MERGING: ' + line)
            for line in o:
                logger.debug('MERGING: ' + line)
            self._add_tlinks_to_fragment(in_fragment, tmp_fragment, out_fragment)
        os.chdir(TTK_ROOT)

        
    def _add_tlinks_to_fragment(self, in_fragment, tmp_fragment, out_fragment):

        """Take the links from the merged tlinks and add them into the fragment. Based on
        the method with the same name in the classifier wrapper."""

        ### The use of self.document.xmldoc here is a bit of a hack. In fact, the
        ### out_fragment is not needed anymore.
        
        xmldoc1 = Parser().parse_file(open(in_fragment,'r'))
        xmldoc2 = Parser().parse_file(open(tmp_fragment,'r'))

        xmldoc1.remove_tags(TLINK)
        self.document.xmldoc.remove_tags(TLINK)
        
        for tlink in xmldoc2.get_tags(TLINK):
            reltype = tlink.attrs[RELTYPE]
            id1 = tlink.attrs.get(EVENT_INSTANCE_ID, None)
            if not id1:
                id1 = tlink.attrs.get(TIME_ID, None)
            if not id1:
                logger.warn("Could not find id1 in " + tlink.content)
            id2 = tlink.attrs.get(RELATED_TO_EVENT_INSTANCE, None)
            if not id2:
                id2 = tlink.attrs.get(RELATED_TO_TIME, None)
            if not id2:
                logger.warn("Could not find id2 in " + tlink.content)
            #origin = CLASSIFIER + ' ' + tlink.attrs.get(CONFIDENCE,'')
            origin = tlink.attrs.get('origin','')
            xmldoc1.add_tlink(reltype, id1, id2, origin)
            self.document.xmldoc.add_tlink(reltype, id1, id2, origin)

        xmldoc1.save_to_file(out_fragment)

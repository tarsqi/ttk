"""Module to create vectors that can be used to train a mallet model.


PRELIMARIES

To run this script you need a gold standard that meets the following
requirements:

- It contains EVENT, TIMEX3 and TLINK tags. The EVENT tags need to have pos,
  tense and aspect attributes

- It contains preprocessor tags s, lex, ng and vg. The lex tags should have pos,
  text and lemma attributes.

- It should have docelement tags.

- It should be in the TTK format.

Here is a minimal example of what an input file should look like:

   <ttk>
   <text>Fido slept on Tuesday.
   </text>
   <metadata>
     <dct value="20160428"/>
   </metadata>
   <source_tags>
     <TEXT id="1" begin="0" end="22" />
   </source_tags>
   <tarsqi_tags>
     <docelement begin="0" end="23" type="paragraph" />
     <s id="s1" begin="0" end="22" />
     <lex id="l1" begin="0" end="4" lemma="Fido" pos="NNP" text="Fido" />
     <ng id="c1" begin="0" end="4" />
     <lex id="l2" begin="5" end="10" lemma="sleep" pos="VBD" text="slept" />
     <vg id="c2" begin="5" end="10" />
     <EVENT begin="5" end="10" aspect="NONE" class="OCCURRENCE" eid="e1" eiid="ei1" pos="VERB" tense="PAST" />
     <lex id="l3" begin="11" end="13" lemma="on" pos="IN" text="on" />
     <lex id="l4" begin="14" end="21" lemma="Tuesday" pos="NNP" text="Tuesday" />
     <ng id="c3" begin="14" end="21" />
     <TIMEX3 begin="14" end="21" origin="GUTIME" tid="t1" type="DATE" value="20160426" />
     <lex id="l5" begin="21" end="22" lemma="." pos="." text="." />
     <TLINK eventInstanceID="ei1" relType="IS_INCLUDED" relatedToTime="t1" />
   </tarsqi_tags>
   </ttk>

One way to get gold standard data is to take the TimeBank 1.2 corpus as released
by the LDC. This corpus is not in the TTK formta and it contains MAKEINSTANCE
tags, but it can be converted by using the utilities/convert.py script.

Then you can run tarsqi.py on the result and create a version with preprocessor
information added:

   $ python tarsqi.py --source=ttk --pipeline=PREPROCESSOR <CONVERTED_TB> <OUT_DIR>


USAGE

To create the vectors, run this script in one of two ways:

   $ python create_vectors.py
   $ python create_vectors.py --gold <OUT_DIR>

In the first invocation, the files in data/gold are used as input. Both
invocations will create two files in the current directory:

   vectors.ee
   vectors.et

Here are two example vectors, one from vectors.ee and one from vectors.et (each
vector is just one line, but below they are spread out over multiple lines for
readability):

   wsj_0006.tml-ei80-ei81 BEFORE e1-asp=NONE e1-cls=ASPECTUAL e1-epos=None
   e1-mod=NONE e1-pol=POS e1-stem=None e1-str=complete e1-tag=EVENT
   e1-ten=PRESENT e2-asp=NONE e2-cls=OCCURRENCE e2-epos=None e2-mod=NONE
   e2-pol=POS e2-stem=None e2-str=transaction e2-tag=EVENT e2-ten=NONE shAsp=0
   shTen=1

   NYT19980402.0453.tml-ei2264-t61 IS_INCLUDED e-asp=NONE e-cls=OCCURRENCE
   e-epos=None e-mod=NONE e-pol=POS e-stem=None e-str=created e-tag=EVENT
   e-ten=PAST t-str=Tuesday t-tag=TIMEX3 t-type=DATE t-value=1998-03-31 order=et
   sig=on

When you run create_vectors.py on TimeBank you will notice a lot of warnings
that tags cannot be inserted. This is a known issue with integrating GUTIME tags
and pre-processor tags which does come at the expense of missing some training
instances for long time expressions.

In any case, as of late April 2016 running this script resulted in 1515 vectors
in vectors.ee and 1029 vectors in vectors.et. These vectors were used to build
the model that ships with the Tarsqi Toolkit.

"""

import os, sys

import path
import root

from tarsqi import Options
from docmodel.document import TarsqiDocument
from docmodel.source_parser import SourceParser
from docmodel.main import create_source_parser
from components.classifier.vectors import collect_tarsqidoc_vectors

from library.main import LIBRARY


GOLD_DIR = os.path.join('data', 'gold')

ee_fh = open("vectors.ee", 'w')
et_fh = open("vectors.et", 'w')

TLINK = LIBRARY.timeml.TLINK
RELTYPE = LIBRARY.timeml.RELTYPE
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
TIME_ID = LIBRARY.timeml.TIME_ID
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME

BEFORE = LIBRARY.timeml.BEFORE
IBEFORE = LIBRARY.timeml.IBEFORE
BEGINS = LIBRARY.timeml.BEGINS
BEGUN_BY = LIBRARY.timeml.BEGUN_BY
DURING = LIBRARY.timeml.DURING
DURING_INV = LIBRARY.timeml.DURING_INV
IS_INCLUDED = LIBRARY.timeml.IS_INCLUDED
SIMULTANEOUS = LIBRARY.timeml.SIMULTANEOUS
IDENTITY = LIBRARY.timeml.IDENTITY
INCLUDES = LIBRARY.timeml.INCLUDES
ENDED_BY = LIBRARY.timeml.ENDED_BY
ENDS = LIBRARY.timeml.ENDS
IAFTER = LIBRARY.timeml.IAFTER
AFTER = LIBRARY.timeml.AFTER

INVERSE = {
    BEFORE: AFTER,
    IBEFORE: IAFTER,
    BEGINS: BEGUN_BY,
    BEGUN_BY: BEGINS,
    IS_INCLUDED: INCLUDES,
    SIMULTANEOUS: SIMULTANEOUS,
    IDENTITY: IDENTITY,
    DURING: DURING_INV,
    DURING_INV: DURING,
    INCLUDES: IS_INCLUDED,
    ENDED_BY: ENDS,
    ENDS: ENDED_BY,
    IAFTER: IBEFORE,
    AFTER: BEFORE
}

# needed for the source parser
options = Options([('--source', 'ttk')])


def process_dir(gold_dir):
    for fname in os.listdir(gold_dir):
        if fname.startswith('.') or fname.endswith('~'):
            continue
        try:
            print fname
            process_file(gold_dir, fname)
        except Exception as e:
            print "WARNING: could not process %s" % fname
            print "        ", sys.exc_info()[1]


def process_file(gold_dir, fname):
    infile = os.path.join(gold_dir, fname)
    source_parser = create_source_parser(options)
    #tarsqidoc = source_parser.parse_file(infile)
    tarsqidoc = TarsqiDocument()
    source_parser.parse_file(infile, tarsqidoc)
    (ee_vectors, et_vectors) = collect_tarsqidoc_vectors(tarsqidoc)
    tlinks = collect_tlinks(tarsqidoc)
    add_reltype_to_vectors(tlinks, ee_vectors, et_vectors)
    write_vectors(ee_vectors, et_vectors)


def add_reltype_to_vectors(tlinks, ee_vectors, et_vectors):
    for v in ee_vectors:
        eiid1 = v.v1.identifier
        eiid2 = v.v2.identifier
        rel = tlinks.get("%s-%s" % (eiid1, eiid2))
        if rel is not None:
            v.relType = rel
    for v in et_vectors:
        eiid = v.v1.identifier
        tid = v.v2.identifier
        rel = tlinks.get("%s-%s" % (eiid, tid))
        if rel is not None:
            v.relType = rel


def collect_tlinks(tarsqidoc):
    tlinks = {}
    for tlink in tarsqidoc.tags.find_tags(TLINK):
        attrs = tlink.attrs
        id1 = attrs.get(EVENT_INSTANCE_ID, attrs.get(TIME_ID))
        id2 = attrs.get(RELATED_TO_EVENT_INSTANCE, attrs.get(RELATED_TO_TIME))
        rel = attrs[RELTYPE]
        # skip disjunctive links
        if not rel.find('|') > -1:
            tlinks["%s-%s" % (id1, id2)] = rel
            tlinks["%s-%s" % (id2, id1)] = INVERSE[rel]
    return tlinks


def write_vectors(ee_vectors, et_vectors):
    """Write those vectors that have a relType that is not None."""
    for v in ee_vectors:
        if v.relType is not None:
            ee_fh.write("%s\n" % v)
    for v in et_vectors:
        if v.relType is not None:
            et_fh.write("%s\n" % v)


if __name__ == '__main__':

    if len(sys.argv) == 3 and sys.argv[1] == '--gold':
        GOLD_DIR = sys.argv[2]
    process_dir(GOLD_DIR)

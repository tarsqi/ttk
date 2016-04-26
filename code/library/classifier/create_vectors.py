"""

Module to create vectors that can be used to train a mallet model.

Preliminaries.

To do this you need a gold standard that meets the following requisites:

- It contains EVENT, TIMEX3 and TLINK tags.

- It contains preprocessor tags s, lex, ng and vg. The lex tags should have pos,
  text and lemma attributes.

- It should have docelement tags.

- It should be in the TTK format.

One way to get this gold standard is to take the TimeBank 1.2 corpus as released
by the LDC. This corpus is not in the TTK formta and it contains MAKEINSTANCE
tags, but it can be converted by using the utilities/convert.py script.

Then you can run tarsqi.py on the result and create a version with preprocessor
information added:

   $ python tarsqi.py --source=ttk --pipeline=PREPROCESSOR <CONVERTED_TB> <OUT_DIR>

Once this is done, you can move the files in <OUT_DIR> to data/gold and run this
script:

   $ python create_vectors.py

This will create two files in the current directory:

   vectors.ee
   vectors.et

If you do not want to move files to data/gold you can use the --gold command
line option:

   $ python create_vectors.py --gold <OUT_DIR>

Results will again be written to vectors.ee and vectors.et.

When you run create_vectors.py on TimeBank you will notice a lot of warnings
that tags cannot be inserted. This is a known issue which does come at the
expense of missing some training instances.

In any case, as of late April 2016 running this script resulted in 1516 vectors
in vectors.ee and 1049 vectors in vectors.et. These vectors were used to build
the model that ships with the Tarsqi Toolkit.

"""

import os, sys

import path
import root

from tarsqi import Options
from docmodel.source_parser import SourceParser
from docmodel.main import create_source_parser
from components.classifier.vectors import collect_tarsqidoc_vectors

from library.timeMLspec import TLINK, RELTYPE, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME
from library.timeMLspec import BEFORE, IBEFORE, BEGINS, BEGUN_BY
from library.timeMLspec import DURING, DURING_INV
from library.timeMLspec import IS_INCLUDED, SIMULTANEOUS, IDENTITY, INCLUDES
from library.timeMLspec import ENDED_BY, ENDS, IAFTER, AFTER

GOLD_DIR = os.path.join('data', 'gold')

ee_fh = open("vectors.ee", 'w')
et_fh = open("vectors.et", 'w')

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

options = Options([('--source', 'ttk')])


def process_dir(gold_dir):
    for fname in os.listdir(gold_dir):
        if fname.startswith('.') or fname.endswith('~'):
            continue
        try:
            print fname
            process_file(gold_dir, fname)
        except:
            print "WARNING: could not process %s" % fname


def process_file(gold_dir, fname):
    infile = os.path.join(gold_dir, fname)
    source_parser = create_source_parser(options)
    tarsqidoc = source_parser.parse_file(infile)
    (ee_vectors, et_vectors) = collect_tarsqidoc_vectors(tarsqidoc)
    tlinks = collect_tlinks(tarsqidoc)
    add_reltype_to_vectors(tlinks, ee_vectors, et_vectors)
    write_vectors(ee_vectors, et_vectors)


def add_reltype_to_vectors(tlinks, ee_vectors, et_vectors):
    for v in ee_vectors:
        eiid1 = v.features["e1-eiid"]
        eiid2 = v.features["e2-eiid"]
        rel = tlinks.get("%s-%s" % (eiid1, eiid2))
        if rel is not None:
            v.relType = rel
    for v in et_vectors:
        eiid = v.features["e-eiid"]
        tid = v.features["t-tid"]
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
        tlinks["%s-%s" % (id1, id2)] = rel
        tlinks["%s-%s" % (id2, id1)] = INVERSE[rel]
    return tlinks


def write_vectors(ee_vectors, et_vectors):
    """Write those vectors that have a relType that is not UNKNOWN."""
    for v in ee_vectors:
        if v.relType != 'UNKNOWN':
            ee_fh.write("%s\n" % v)
    for v in et_vectors:
        if v.relType != 'UNKNOWN':
            et_fh.write("%s\n" % v)


if __name__ == '__main__':

    if len(sys.argv) == 3 and sys.argv[1] == '--gold':
        GOLD_DIR = sys.argv[2]
    process_dir(GOLD_DIR)

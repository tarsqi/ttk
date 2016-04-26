"""

Some conversion utilities.

The following can be run from the command line:

   $ convert.py --convert-timebank -i INDIR -o OUTDIR

   Converts TimeBank 1.2 as released by LDC into a version without makeinstance
   tags using the TTK format.

"""

import os, sys, getopt

import path
import tarsqi

from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser

from library.timeMLspec import TIMEX, EVENT, EID, EIID, EVENTID
from library.timeMLspec import SIGNAL, ALINK, SLINK, TLINK

MAKEINSTANCE = 'MAKEINSTANCE'

TIMEML_TAGS = (TIMEX, EVENT, MAKEINSTANCE, SIGNAL, ALINK, SLINK, TLINK)


def load(infile):
    options = tarsqi.Options([('--source', 'timebank')])
    source_parser = create_source_parser(options)
    metadata_parser = create_metadata_parser(options)
    docstructure_parser = create_docstructure_parser()
    tarsqidoc = source_parser.parse_file(infile)
    metadata_parser.parse(tarsqidoc)
    docstructure_parser.parse(tarsqidoc)
    tarsqidoc.add_options(options)
    for tagname in TIMEML_TAGS:
        tarsqidoc.tags.import_tags(tarsqidoc.source.tags, tagname)
        tarsqidoc.source.tags.remove_tags(tagname)
    return tarsqidoc


def convert_timebank(timebank_dir, out_dir):
    for fname in os.listdir(timebank_dir):
        print fname
        infile = os.path.join(timebank_dir, fname)
        outfile = os.path.join(out_dir, fname)
        convert_timebank_file(infile, outfile)


def convert_timebank_file(infile, outfile):
    tarsqidoc = load(infile)
    events = tarsqidoc.tags.find_tags(EVENT)
    instances = tarsqidoc.tags.find_tags(MAKEINSTANCE)
    instances = { i.attrs.get(EVENTID): i for i in instances }
    for event in events:
        instance = instances[event.attrs[EID]]
        del instance.attrs[EVENTID]
        event.attrs.update(instance.attrs)
    tarsqidoc.tags.remove_tags(MAKEINSTANCE)
    tarsqidoc.print_all(outfile)


if __name__ == '__main__':

    long_options = ['convert-timebank']
    (opts, args) = getopt.getopt(sys.argv[1:], 'i:o:', long_options)
    opts = { k: v for k, v in opts }

    if '--convert-timebank' in opts:
        convert_timebank(opts['-i'], opts['-o'])

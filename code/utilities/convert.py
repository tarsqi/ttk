"""Some conversion utilities.

1. Convert LDC TimeBank into a modern TimeBank in the TTK format.

The following command can be run from the command line from the directory this
file is in:

   $ python convert.py --convert-timebank -i INDIR -o OUTDIR

   Converts TimeBank 1.2 as released by LDC into a version without makeinstance
   tags using the TTK format. This should be run on the data/extra files in the
   LDC distribution because those have the metadata that allow the TimeBank meta
   data parser to find the DCT.

"""

import os, sys, getopt

import path
import tarsqi
from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser
from docmodel.document import TarsqiDocument
from library.main import TarsqiLibrary


LIBRARY = TarsqiLibrary()

TIMEX = LIBRARY.timeml.TIMEX
EVENT = LIBRARY.timeml.EVENT
SIGNAL = LIBRARY.timeml.SIGNAL
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK

EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
EVENTID = LIBRARY.timeml.EVENTID

MAKEINSTANCE = 'MAKEINSTANCE'

TIMEML_TAGS = (TIMEX, EVENT, MAKEINSTANCE, SIGNAL, ALINK, SLINK, TLINK)


def convert_timebank(timebank_dir, out_dir):
    """Take the LDC TimeBank files in timebank_dir and create timebank files in
    out_dir that are in the TTK format and do not have MAKEINSTANCE tags."""
    # make the paths absolute so we do not get bitten by Tarsqi's habit of
    # changing the current directory
    timebank_dir = os.path.abspath(timebank_dir)
    out_dir = os.path.abspath(out_dir)
    for fname in os.listdir(timebank_dir):
        if fname.endswith('.tml'):
            print fname
            _convert_timebank_file(os.path.join(timebank_dir, fname),
                                   os.path.join(out_dir, fname))


def _convert_timebank_file(infile, outfile):
    opts = [("--source", "timebank"), ("--loglevel", "2"), ("--trap-errors", "False")]
    t = tarsqi.Tarsqi(opts, infile, None)
    t.source_parser.parse_file(t.input, t.tarsqidoc)
    t.metadata_parser.parse(t.tarsqidoc)
    for tagname in TIMEML_TAGS:
        t.tarsqidoc.tags.import_tags(t.tarsqidoc.source.tags, tagname)
        t.tarsqidoc.source.tags.remove_tags(tagname)
    events = t.tarsqidoc.tags.find_tags(EVENT)
    instances = t.tarsqidoc.tags.find_tags(MAKEINSTANCE)
    instances = { i.attrs.get(EVENTID): i for i in instances }
    for event in events:
        instance = instances[event.attrs[EID]]
        del instance.attrs[EVENTID]
        event.attrs.update(instance.attrs)
    t.tarsqidoc.tags.remove_tags(MAKEINSTANCE)
    t.tarsqidoc.print_all(outfile)


if __name__ == '__main__':

    long_options = ['convert-timebank']
    (opts, args) = getopt.getopt(sys.argv[1:], 'i:o:', long_options)
    opts = { k: v for k, v in opts }
    if '--convert-timebank' in opts:
        convert_timebank(opts['-i'], opts['-o'])

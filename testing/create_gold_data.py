"""create_gold_data.py

Create a gold standard in TTK format from a corpus of TimeML files.

STEPS:

- Convert Timebank into the TTK format

   $ python -m utilities.convert --timebank2ttk TIMEBANK_DIR TTK_DIR

   TIMEBANK_DIR = /Users/Shared/DATA/resources/corpora/timebank/2007/ldc-distribution/timebank_1.2/data/extra
   TTK_DIR = data/gold/timebank

NOTE: all the code below seems to be superfluous now.

"""


from __future__ import absolute_import
from __future__ import print_function
import os, sys

import tarsqi
from docmodel.document import TarsqiDocument
from docmodel.source_parser import SourceParserXML
from utilities import logger

logger.initialize_logger('log', level=3)

TIMEBANK_DIR = '/Users/Shared/DATA/resources/corpora/timebank/'
SOURCE_DATA_DIR = TIMEBANK_DIR + '2007/ldc-distribution/timebank_1.2/data/timeml'
GOLD_DATA_DIR = 'evaluation/data/gold'


parser = SourceParserXML()

def process_dir(directory):
    for fname in os.listdir(directory):
        if not fname.endswith('.tml'):
            continue
        process_file(directory, fname)
        break

def process_file(directory, fname):
    logger.info(fname)
    infile = os.path.join(directory, fname)
    outfile = os.path.join(GOLD_DATA_DIR, fname)
    tarsqidoc = TarsqiDocument()
    tarsqidoc.add_options(tarsqi.Options([("--target-format", "ttk")]))
    parser.parse_file(infile, tarsqidoc)
    for element in tarsqidoc.elements():
        # move the source_tags to the tarsqi_tags
        source_tags = element.source_tags
        tarsqi_tags = element.tarsqi_tags
        element.source_tags = tarsqi_tags
        element.tarsqi_tags = source_tags
    tarsqidoc.print_all(outfile)


if __name__ == '__main__':
    process_dir(SOURCE_DATA_DIR)



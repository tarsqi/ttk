"""

Main module for the TLink merging component.

"""

import os
import time

from components.common_modules.component import TarsqiComponent
from library.tarsqi_constants import LINK_MERGER
from utilities import logger
from utilities.sputlink.main import ConstraintPropagator

TTK_ROOT = os.environ['TTK_ROOT']

DEBUGGING = False


class LinkMerger (TarsqiComponent):

    """Class that implements the LinkMerger.

    Instance variables:
       NAME - a string
       compositions_file - filename of the compositions file"""
    
    def __init__(self):
        """Set the NAME and the compositions_file instance variables."""
        self.NAME = LINK_MERGER
        # TODO: compositions_file should be defined by SputLink
        self.compositions_file = os.path.join(TTK_ROOT, 'utilities', 'sputlink',
                                              'rules', 'compositions_short.txt')
        
    def process(self, infile, outfile):
        """Process a fragment file and write a file with EVENT tags.
        Arguments:
           infile - an absolute path
           outfile - an absolute path"""
        propagator = ConstraintPropagator()
        propagator.setup(open(self.compositions_file), open(infile))
        propagator.add_constraints()
        if DEBUGGING:
            (f1, f2) = self._get_graphfile_names(infile)
            propagator.pp_graph(f1)
        propagator.reduce_graph()
        if DEBUGGING:
            propagator.pp_graph(f2)
        propagator.create_output(outfile)
        
    def _get_graphfile_names(self, infile):
        """Return a pair of names for graph files, based on the infile name."""
        filename = infile.split(os.sep).pop()
        filename = "graph-%s" % filename[9:12]
        TMP_DIR = os.path.join(TTK_ROOT, 'data', 'tmp')
        graph1 =  os.path.join(TMP_DIR, filename+'-c.html')
        graph2 =  os.path.join(TMP_DIR, filename+'-r.html')
        return (graph1, graph2)    

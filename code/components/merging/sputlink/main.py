
import os

from graph import Graph
from objects import Constraint
from mappings import translate_timeml_relation, invert_interval_relation
from utils import CompositionTable
from utils import html_graph_prefix
from library.timeMLspec import TLINK, EVENT, TIMEX, TID, EIID
from library.timeMLspec import CONFIDENCE, ORIGIN
from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME

DEBUG = False
DEBUG = True

TTK_ROOT = os.environ['TTK_ROOT']

COMPOSITIONS = os.path.join(TTK_ROOT, 'components', 'merging', 'sputlink',
                            'rules', 'compositions_short.txt')


class ConstraintPropagator:

    """Main SputLink class. Instance variables:

    filename      -  a string
    graph         -  a Graph
    pending       -  a queue of links to be added
    compositions  -  a CompositionTable

    """

    def __init__(self, tarsqidoc):
        """Read the compositions table and export the compositions to the
        graph. Read the TimeML file and send the events and timexes to the
        graph, then use the tlinks to build the pending queue."""
        self.filename = tarsqidoc.source.filename
        self.compositions = CompositionTable(COMPOSITIONS)
        self.graph = Graph(self.filename, self.compositions)
        self.pending = []
        self._debug_init_cycles_file()
        self._debug_print_compositions_file()
        self.graph.add_nodes(tarsqidoc.tags.find_tags(EVENT),
                             tarsqidoc.tags.find_tags(TIMEX))

    def queue_constraints(self, tlinks):
        """Take a list of tlinks, encoded as Tag elements, and add them to the
        pending queue as instances of Constraint."""
        for tlink in tlinks:
            if RELTYPE not in tlink.attrs:
                continue
            id1 = tlink.attrs.get(EVENT_INSTANCE_ID) \
                or tlink.attrs[TIME_ID]
            id2 = tlink.attrs.get(RELATED_TO_EVENT_INSTANCE) \
                or tlink.attrs[RELATED_TO_TIME]
            rel = translate_timeml_relation(tlink.attrs[RELTYPE])
            rel_i = invert_interval_relation(rel)
            # add the user constraint and its inverse; without the latter, even
            # when all user links are on one side of the graphs, we do not find
            # all new constraints (TODO: find out why)
            c1 = Constraint(id1, rel, id2, source='user', history=tlink)
            c2 = Constraint(id2, rel_i, id1, source='user-inverted', history=c1)
            self.pending.extend([c1, c2])

    def reset(self):
        """Reset the file, graph and pending instance variables."""
        self.filename = None
        self.graph = Graph()
        self.pending = []

    def propagate_constraints(self, force=False, threshold=0):
        """Get all constraints from the pending queue and ask the graph to propagate
        them one by one."""
        while self.pending:
            constraint = self.pending.pop(0)
            self.graph.propagate(constraint)
            self._debug_print_cycle(constraint)

    def reduce_graph(self):
        """Ask the graph to reduce itself."""
        self.graph.reduce()
        self._debug_print_cycle("Graph reduction")

    def _debug_init_cycles_file(self):
        if DEBUG:
            tmp_dir = os.path.join(TTK_ROOT, 'data', 'tmp')
            cycles_file = os.path.join(tmp_dir, 'cycles.html')
            self.cycles_fh = open(cycles_file, 'w')
            html_graph_prefix(self.cycles_fh)

    def _debug_print_cycle(self, constraint=None):
        if DEBUG:
            fname = "cycle-%02d.html" % self.graph.cycle
            self.cycles_fh.write("<p>Cycle %s - <b>%s</b></p>\n"
                                 % (self.graph.cycle, constraint))
            graph_file = os.path.join(TTK_ROOT, 'data', 'tmp', fname)
            self.graph.pp_html(filehandle=self.cycles_fh)

    def _debug_print_compositions_file(self):
        if DEBUG:
            tmp_dir = os.path.join(TTK_ROOT, 'data', 'tmp')
            comp_file = os.path.join(tmp_dir, 'compositions.html')
            self.compositions.pp(comp_file)

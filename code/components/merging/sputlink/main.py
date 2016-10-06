
import os

from graph import Graph
from objects import Constraint
from mappings import translate_timeml_relation, invert_interval_relation
from utils import CompositionTable
from utils import html_graph_prefix
from library.main import LIBRARY

DEBUG = False
DEBUG = True

TTK_ROOT = os.environ['TTK_ROOT']

COMPOSITIONS = os.path.join(TTK_ROOT, 'components', 'merging', 'sputlink',
                            'rules', 'compositions_short.txt')

TLINK = LIBRARY.timeml.TLINK
RELTYPE = LIBRARY.timeml.RELTYPE
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
TIME_ID = LIBRARY.timeml.TIME_ID
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME
CONFIDENCE = LIBRARY.timeml.CONFIDENCE
ORIGIN = LIBRARY.timeml.ORIGIN

EVENT = LIBRARY.timeml.EVENT
EIID = LIBRARY.timeml.EIID

TIMEX = LIBRARY.timeml.TIMEX
TID = LIBRARY.timeml.TID


class ConstraintPropagator:

    """Main SputLink class. Instance variables:

    filename      -  a string
    graph         -  a Graph
    pending       -  a queue of links to be added
    compositions  -  a CompositionTable

    """

    def __init__(self, tarsqidoc=None, constraints=None):
        """Read the compositions table, export the compositions to the graph,
        and add nodes to the graph. Either tarsqidoc or constraints has to be
        not None."""
        self.compositions = CompositionTable(COMPOSITIONS)
        self.graph = Graph(self.compositions)
        self.pending = []
        self._debug_init_cycles_file()
        self._debug_print_compositions_file()
        if tarsqidoc is not None:
            self.graph.add_nodes(tarsqidoc.tags.find_tags(EVENT), EVENT)
            self.graph.add_nodes(tarsqidoc.tags.find_tags(TIMEX), TIMEX)
        else:
            nodes = [c[0] for c in constraints] + [c[2] for c in constraints]
            self.graph.add_nodes(set(nodes), 'IDENTIFIER')

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

    def queue_test_constraints(self, constraints):
        """Take a list of test constrains, encoded as tuples, and add them to
        the pending queue as instances of Constraint. Same as above, but now
        used for testing."""
        for (n1, rel, n2) in constraints:
            rel_i = invert_interval_relation(rel)
            c1 = Constraint(n1, rel, n2, source='user')
            c2 = Constraint(n2, rel_i, n1, source='user-inverted')
            self.pending.extend([c1, c2])

    def reset(self):
        """Reset the graph and pending instance variables."""
        self.graph = Graph()
        self.pending = []

    def propagate_constraints(self):
        """Get all constraints from the pending queue and ask the graph to propagate
        them one by one."""
        while self.pending:
            constraint = self.pending.pop(0)
            self.graph.propagate(constraint)
            self._debug_print_cycle(constraint)

    def collect_edges(self):
        return self.graph.get_edges()

    def reduce_graph(self):
        """Ask the graph to reduce itself."""
        self.graph.reduce()
        self._debug_print_cycle("Graph reduction")

    def close_cycle_debug_file(self):
        """This is useful if you run the tests while debugging is on. Without it
        the cycles file may contain partially overwritten older cycles."""
        # TODO: I am not sure why this happens though since I open a file in w
        # mode at the beginning of each test.
        if self.cycles_fh is not None:
            self.cycles_fh.close()

    def _debug_init_cycles_file(self):
        self.cycles_fh = None
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

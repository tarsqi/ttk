
import os

from graph import Graph
from objects import Constraint
from mappings import invert_timeml_relation
from mappings import translate_timeml_relation
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

    """Main SputLink class. Instance variables are: (1) file, a file object (2)
    grap, a Graph, (3) pending, a list of links, the first one will be added
    first and (4) compositions, a CompositionTable."""

    def __init__(self, tarsqidoc):
        """Read the compositions table and export the compositions to the
        graph. Read the TimeML file and send the events and timexes to the
        graph, then use the tlinks to build the pending queue."""
        self.filename = tarsqidoc.source.filename
        self.compositions = CompositionTable(COMPOSITIONS)
        self.graph = Graph(self.filename, self.compositions)
        self.pending = []
        if DEBUG:
            self._debug_init_cycles_file()
            self._debug_print_compositions_file()
        self.graph.add_nodes(tarsqidoc.tags.find_tags(EVENT),
                             tarsqidoc.tags.find_tags(TIMEX))

    def queue_constraints(self, tlinks):
        """Take a list of tlinks, encoded as Tag elements, and add them to the
        pending queue as instances of Constraint."""
        for tlink in tlinks:
            # if not tlink.attrs.has_key(RELTYPE):
            if RELTYPE not in tlink.attrs:
                continue
            id1 = tlink.attrs.get(EVENT_INSTANCE_ID) \
                or tlink.attrs[TIME_ID]
            id2 = tlink.attrs.get(RELATED_TO_EVENT_INSTANCE) \
                or tlink.attrs[RELATED_TO_TIME]
            rel = translate_timeml_relation(tlink.attrs[RELTYPE])
            rel_i = invert_timeml_relation(tlink.attrs[RELTYPE])
            rel_i = translate_timeml_relation(rel_i)
            # add the user constraint and its inverse, without the latter, even
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
        """Add all constraints on the queue to the graph and propagate them in
        turn. Currently hands all constraints to the graph. A later version will
        either use a confidence threshold under which constraints will not be
        added or some other mechanism to create the pending queue. Also, the
        force parameter is not yet used."""
        while self.pending:
            self._propagate_constraint()

    def _propagate_constraint(self):
        """Pop a Constraint from the pending list if it is not empty and ask
        the graph to propagate it.."""
        if self.pending:
            constraint = self.pending.pop(0)
            self.graph.propagate(constraint)
            if DEBUG:
                fname = "cycle-%02d.html" % self.graph.cycle
                self.cycles_fh.write("<p>Cycle %s - <b>%s</b></p>\n"
                                     % (self.graph.cycle, constraint))
                graph_file = os.path.join(TTK_ROOT, 'data', 'tmp', fname)
                self.pp_graph(filehandle=self.cycles_fh)

    def reduce_graph(self):
        """Ask the graph to reduce itself."""
        self.graph.reduce()

    def pp_graph(self, filename=None, filehandle=None):
        """Print the graph in an HTML table."""
        self.graph.pp(filename=filename, filehandle=filehandle)

    def pp_compositions(self, filename):
        """Print the composition table to an HTML table."""
        self.compositions.pp(filename)

    def _debug_init_cycles_file(self):
        tmp_dir = os.path.join(TTK_ROOT, 'data', 'tmp')
        cycles_file = os.path.join(tmp_dir, 'cycles.html')
        self.cycles_fh = open(cycles_file, 'w')
        html_graph_prefix(self.cycles_fh)

    def _debug_print_compositions_file(self):
        tmp_dir = os.path.join(TTK_ROOT, 'data', 'tmp')
        comp_file = os.path.join(tmp_dir, 'compositions.html')
        self.compositions.pp(comp_file)

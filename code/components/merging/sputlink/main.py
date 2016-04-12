
import os

from graph import Graph
from objects import Constraint
from mappings import invert_timeml_relation
from mappings import translate_timeml_relation
from utils import CompositionTable
from utils import html_graph_prefix
from library.timeMLspec import TLINK, EVENT, TIMEX, TID, EIID
from library.timeMLspec import RELTYPE, EVENT_INSTANCE_ID, TIME_ID, CONFIDENCE
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE, RELATED_TO_TIME, ORIGIN

DEBUG = False
DEBUG = True

TTK_ROOT = os.environ['TTK_ROOT']

COMPOSITIONS = os.path.join(TTK_ROOT, 'components', 'merging', 'sputlink',
                            'rules', 'compositions_short.txt')


class ConstraintPropagator:

    """Main SputLink class.
    
    Instance variables:
       file - a file object
       xmldoc - the Xml document created from the file
       grap - a Graph
       pending - a list of links, the first one will be added first
       compositions - a CompositionTable
    """
    
    def __init__(self, tarsqidoc):
        """Read the compositions table and export the compositions to the
        graph. Read the TimeML file and send the events and timexes to the
        graph, then use the tlinks to build the pending queue."""
        self.file = tarsqidoc.source.filename
        self.graph = Graph()
        self.pending = []
        self.compositions = CompositionTable(COMPOSITIONS)
        self.graph.compositions = self.compositions
        if DEBUG:
            cycles_file = os.path.join(TTK_ROOT, 'data', 'tmp', 'cycles.html')
            self.cycles_fh = open(cycles_file, 'w')
            html_graph_prefix(self.cycles_fh)
        self.file = tarsqidoc.source.filename
        self.graph.file = self.file
        events = tarsqidoc.tags.find_tags(EVENT)
        timexes = tarsqidoc.tags.find_tags(TIMEX)
        tlinks = tarsqidoc.tags.find_tags(TLINK)
        self.graph.add_nodes(events, timexes)
        self._initialize_queue(tlinks)

    def _initialize_queue(self, tlinks):
        """Take a list of tlinks, encoded as Tag elements, and add them to the
        pending queue as instances of Constraint."""
        for tlink in tlinks:
            if not tlink.attrs.has_key(RELTYPE):
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
        self.file = None
        self.graph = Graph()
        self.pending = []

    def add_constraint(self):
        """Pop a Constraint from the pending list if it is not empty and ask
        the graph to propagate it.."""
        if self.pending:
            constraint = self.pending.pop(0)
            self.graph.propagate(constraint)
            if DEBUG:
                fname = "cycle-%02d.html" % self.graph.cycle
                self.cycles_fh.write("<p>Cycle %s - %s</p>\n"
                                     % (self.graph.cycle, constraint))
                graph_file = os.path.join(TTK_ROOT, 'data', 'tmp', fname)
                self.pp_graph(filehandle=self.cycles_fh)

    def add_constraints(self, force=False, threshold=0):
        """Add all constraints to the graph, which will propagate them in
        turn. Currently hands all constraints to the graph. A later
        version will either use a confidence threshold under which
        constraints will not be added or some other mechanism to
        create the pending queue. Also, the force parameter is not yet
        used."""
        while self.pending:
            self.add_constraint()

    def reduce_graph(self):
        """Ask the graph to reduce itself."""
        self.graph.reduce()

    def update_tarsqidoc(self):
        return
        for n1, rest in self.graph.edges.items():
            for n2, edge in self.graph.edges[n1].items():
                if edge.constraint is not None:
                    print edge, edge.constraint.source

    def pp_graph(self, filename=None, filehandle=None):
        """Print the graph in an HTML table."""
        self.graph.pp(filename=filename, filehandle=filehandle)

    def pp_compositions(self, filename):
        """Print the composition table to an HTML table."""
        self.compositions.pp(filename)

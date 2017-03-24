from utils import intersect_lists
from utils import intersect_relations
from utils import compare_id
from library.main import LIBRARY

TIMEX = LIBRARY.timeml.TIMEX
TID = LIBRARY.timeml.TID
EVENT = LIBRARY.timeml.EVENT
EIID = LIBRARY.timeml.EIID
FORM = LIBRARY.timeml.FORM
VALUE = LIBRARY.timeml.VALUE

SIMPLE_RELS = ('<', 'm', 'di', 'si', 'fi', '=', '>', 'mi', 'd', 's', 'f')
NORMALIZED_RELS = ('<', 'm', 'di', 'si', 'fi', '=')

NORMALIZED_RELATIONS = {rel: True for rel in NORMALIZED_RELS}
SIMPLE_RELATIONS = {rel: True for rel in SIMPLE_RELS}


class Node:

    """Implements the node objects of the graph.

    Instance variables:
       id           -  an eiid, tid or other identifier
       text         -  string from the document or empty string
       source       -  a Tag or an identifier
       source-type  -  'TIMEX3', 'EVENT', or 'IDENTIFIER'
       edges_in     -  a hash indexed on node ids
       edges_out    -  a hash indexed on node ids

    The source and source-type attributes encode what element or elements the
    Node was created from. If source-type is TIMEX or EVENT then source is a
    single tag.

    But if source-type is 'class', then the Node implements an equivalence set
    of time expressions and events, that is, a set defined by the = interval
    relation. The source attribute than is a list of tuples, where each tuple
    contains (i) a Tag, (ii) a pair of interval relation and TimeML relation,
    and (iii) another XmlDocElement or pair of XmlDocElements. The very first
    Node in the entire list is the class representative. (TODO: is this still
    relevant?)

    """

    def __init__(self, source, identifier, source_type, text):
        """Initialize from a timex, an event or simply an identifier, using tid,
        eiid or the identifier for the node identifier. Set edges_in and
        edges_out to the empty hash."""
        self.source = source
        self.source_type = source_type
        self.id = identifier
        self.text = text
        self.edges_in = {}
        self.edges_out = {}

    def __str__(self):
        """Returns string in "<Node id text>" format."""
        return "<Node %s '%s'>" % (self.id, self.text)

    def pretty_print(self):
        """Print the node with its edges_in and edges_out attributes to standard
        output."""
        print "\n", self
        e_in = self.edges_in.keys()
        e_out = self.edges_out.keys()
        e_in.sort(compare_id)
        e_out.sort(compare_id)
        print "  i [%s]" % (' '.join(e_in))
        print "  o [%s]" % (' '.join(e_out))


class Edge:

    """Implements the edges of the graph.

    Instance variables:
       id           -  the node identifier
       node1        -  an eiid, tid or other identifier
       node2        -  an eiid, tid or other identifier
       graph        -  the Graph the edge is in
       constraint   -  None or the current Constraint on the edge
       relset       -  None or the value of constraint.relset
       constraints  -  history of Constraints, a list
    """

    def __init__(self, n1, n2, graph):
        """Initialize from two node identifiers and the graph."""
        self.id = "%s-%s" % (n1, n2)
        self.node1 = n1
        self.node2 = n2
        self.graph = graph
        self.constraint = None
        self.relset = None
        self.constraints = []

    def __str__(self):
        return "<Edge %s {%s} %s>" % (self.node1, str(self.relset), self.node2)

    def get_node1(self):
        """retrun the Node object for node1."""
        return self.graph.nodes[self.node1]

    def get_node2(self):
        """retrun the Node object for node2."""
        return self.graph.nodes[self.node2]

    def add_constraint(self, constraint):
        """Set the constaint attribute and append to the constraints
        attribute."""
        self.constraint = constraint
        self.relset = constraint.relset
        self.constraints.append(constraint)

    def remove_constraint(self):
        """Remove the constraint from the edge. Also updates the edges_in and
        edges_out attributes on the source and target node."""
        self.constraint = None
        self.relset = None
        node1 = self.get_node1()
        node2 = self.get_node2()
        # print self.node1, 'o',  node1.edges_out.keys()
        # print self.node2, 'i',  node2.edges_out.keys()
        del node1.edges_out[self.node2]
        del node2.edges_in[self.node1]

    def is_derived(self):
        """Returns True if the constraint on the edge was derived by closure."""
        return self.constraint.source not in ('user', 'user-inverted')


class Constraint:

    """An object representing the constraint on an edge.

    Instance variables:
       node1 - an eiid or tid
       node2 - an eiid or tid
       relset - a string
       edge - the Edge the constraint is expressed on
       cycle - an integer, the closure cycle in which the constraint was created
       source -
       graph -
       history -
    """

    def __init__(self, id1, rels, id2, cycle=None, source=None, history=None):
        self.node1 = id1
        self.node2 = id2
        self.relset = rels
        self.edge = None
        self.graph = None
        self.cycle = cycle
        self.source = source
        self.history = history

    def __str__(self):
        rels = str(self.relset)
        return "%s {%s} %s" % (self.node1, rels, self.node2)

    def get_node1(self):
        """Retrieve the node1 object from the edge."""
        return self.edge.get_node1()

    def get_node2(self):
        """Retrieve the node2 object from the edge."""
        return self.edge.get_node2()

    def is_garbage(self):
        """Return True if the constraint is useless and potentially damaging to the
        algorithm. We don't like constraints like [e1 < e1]."""
        return self.node1 == self.node2

    def is_disjunction(self):
        """Return True if the relation set is a disjunction, return False
        otherwise."""
        if self.relset.find(' ') > -1:
            return True
        return False

    def has_simple_relation(self):
        """Return True if the relation is one of the non-disjunctive ones,
        return False otherwise."""
        return SIMPLE_RELATIONS.get(self.relset, False)

    def has_normalized_relation(self):
        """Return True if the relation is one of the normalized ones, return
        False otherwise."""
        return NORMALIZED_RELATIONS.get(self.relset, False)

    def pp_history(self, indent=''):
        if isinstance(self.history, tuple):
            print("%s%s" % (indent, str(self.history[0])))
            print("%s%s" % (indent, str(self.history[1])))
        elif self.history.__class__.__name__ == 'Tag':
            tlink = "TLINK(relType=%s)" % self.history.attrs.get('relType')
            print("%s%s" % (indent, tlink))
        elif self.history.__class__.__name__ == 'Constraint':
            print("%s%s" % (indent, self.history))
        else:
            print("%sno history" % indent)

    def history_string(self):
        if isinstance(self.history, tuple):
            return "[%s] and [%s]" % (str(self.history[0]), str(self.history[1]))
        elif self.history.__class__.__name__ == 'Tag':
            return "TLINK(relType=%s)" % self.history.attrs.get('relType')
        elif self.history.__class__.__name__ == 'Constraint':
            return "[%s]" % self.history
        else:
            return "None"

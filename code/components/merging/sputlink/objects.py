from utils import intersect_lists
from utils import intersect_relations
from utils import compare_id
from library.timeMLspec import TID, EIID, TIMEX, EVENT, FORM, VALUE


SIMPLE_RELS = ('<', 'm', 'di', 'si', 'fi', '=', '>', 'mi', 'd', 's', 'f')
NORMALIZED_RELS = ('<', 'm', 'di', 'si', 'fi', '=')

NORMALIZED_RELATIONS = {rel: True for rel in NORMALIZED_RELS}
SIMPLE_RELATIONS = {rel: True for rel in SIMPLE_RELS}


class Node:

    """Implements the node objects of the graph.

    Instance variables:
       id - an eiid or tid
       text - string from the document
       source - a Tag (or something else??)
       source-type - 'timex', 'event', 'set'
       edges_in - a hash indexed on node ids
       edges_out - a hash indexed on node ids

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

    def __init__(self, timex=None, event=None):
        """Initialize from a timex or from an event-instance pair, using tid
        or eiid. Set edges_in and edges_out to the empty hash."""
        if timex:
            self.id = timex.attrs[TID]
            self.text = timex.attrs[VALUE]
            self.source = timex
            self.source_type = TIMEX
        elif event:
            self.id = event.attrs[EIID]
            self.text = event.attrs[FORM]
            self.source = event
            self.source_type = EVENT
        self.edges_in = {}
        self.edges_out = {}

    def pretty_print(self):
        """Print the node with its edges_in and edges_out attributes to
        standard output."""
        print "\n", self
        e_in = self.edges_in.keys()
        e_out = self.edges_out.keys()
        e_in.sort(compare_id)
        e_out.sort(compare_id)
        print "  i [%s]" % (' '.join(e_in))
        print "  o [%s]" % (' '.join(e_out))

    def __str__(self):
        """Return a string in [self.id] format."""
        return "[%s '%s']" % (self.id, self.text)


class Edge:

    """Implements the edges of the graph.

    Instance variables:
       id - concatenation of node ids
       node1 - an eiid or tid
       node2 - an eiid or tid
       graph - the Graph the edge is in
       constraint - None or the current Constraint on the edge
       relset - None or the value of constraint.relset
       constraints - history of Constraints, a list
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
        return "<< %s {%s} %s >>" % (self.node1, str(self.relset), self.node2)

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


    def is_derivable(self):

        """Returns True if the constraint on the edge can be derived from
        other constraints, returns False otherwise."""

        if self.constraint.source == 'closure':
            return True

        # Get all the nodes k such that Edge(n1,k) and Edge(k,n2)
        n1 = self.get_node1()
        n2 = self.get_node2()
        intersection = intersect_lists(n1.edges_out.keys(), n2.edges_in.keys())

        debug = True
        debug = False
        if debug:
            print
            print self
            n1.pretty_print()
            n2.pretty_print()
            # intersection.sort(compare_id)
            print "\n  Intersection: [%s]\n" % ' '.join(intersection)

        # For all nodes k, get the composition of c(n1,k) with c(k,n2)
        aggregate_intersection = None
        for k in intersection:
            c_n1_k = self.graph.edges[self.node1][k].constraint
            c_k_n2 = self.graph.edges[k][self.node2].constraint
            composition = self.graph.compositions.compose_rels(c_n1_k.relset,
                                                               c_k_n2.relset)
            if debug:
                print "  %s + %s = %s" % (c_n1_k, c_k_n2, composition)
            if composition == self.relset:
                if debug:
                    print "  DERIVABLE FROM ONE COMPOSITION"
                return True
            else:
                aggregate_intersection = \
                    intersect_relations(aggregate_intersection,
                                        composition)
                if debug:
                    print "  aggregate: %s" % aggregate_intersection
                if aggregate_intersection == self.relset:
                    if debug:
                        print "  DERIVABLE FROM AGGREGATE COMPOSITION"
                    return True
            # Get the intersection of all compositions

        # If this intersection is equal to the constraint c(n1,n2),
        # then c(n1,n2) is derivable

        return False


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
        mapping = {'user': 'u', 'user-inverted': 'ui',
                   'closure': 'c', 'closure-inverted': 'ci'}
        source = mapping.get(self.source, self.source)
        return "[%s {%s} %s - %s]" % (self.node1, rels, self.node2, source)

    def get_node1(self):
        """Retrieve the node1 object from the edge."""
        return self.edge.get_node1()

    def get_node2(self):
        """Retrieve the node2 object from the edge."""
        return self.edge.get_node2()

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

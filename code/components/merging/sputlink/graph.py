"""

Implements the Graph object which is used by the ConstraintPropagator.

It is here where Allen's constraint propagation algorithm is implemented.

"""

# TODO: I am not convinced that the history mechanism is very good, yet it seems
# to be sufficient for our current purposes.


from objects import Node, Edge, Constraint
from utils import intersect_relations
from utils import compare_id
from utils import html_graph_prefix
from mappings import invert_interval_relation
from mappings import abbreviate_convex_relation
from utilities import logger
from library.main import LIBRARY

DEBUG = True
DEBUG = False

TIMEX = LIBRARY.timeml.TIMEX
TID = LIBRARY.timeml.TID
EVENT = LIBRARY.timeml.EVENT
EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
EVENTID = LIBRARY.timeml.EVENTID
FORM = LIBRARY.timeml.FORM
VALUE = LIBRARY.timeml.VALUE


class Graph:

    """Implements the graph object used in the constraint propagation algorithm.

    Instance variables:
       filename      -  the name of the source file
       cycle         -  an integer
       queue         -  a list of Constraints
       nodes         -  a hash of Nodes, indexed on node identifiers
       edges         -  a hash of hashes of Edges, indexed on node identifiers
       compositions  -  a CompositionTable
    """

    def __init__(self, compositions):
        """Initialize an empty graph, with empty queue, nodes dictionary and
        edges dictionary."""
        self.compositions = compositions
        self.cycle = 0
        self.queue = []
        self.nodes = {}
        self.edges = {}

    def add_nodes(self, events, timexes):
        """Adds the events/instances and timexes to the nodes table. Also
        initializes the edges table now that all nodes are known."""
        for timex in timexes:
            node = Node(timex=timex)
            self.nodes[node.id] = node
        for event in events:
            node = Node(event=event)
            self.nodes[node.id] = node
        for n1 in self.nodes.keys():
            self.edges[n1] = {}
            for n2 in self.nodes.keys():
                self.edges[n1][n2] = Edge(n1, n2, self)

    def add_nodes(self, sources, source_type):
        """Creates Nodes for each source and add them to the nodes table. Also
        initializes the edges table now that all nodes are known. A source is
        either an event or timex tag or simply an identifier."""
        for source in sources:
            if source_type == 'IDENTIFIER':
                identifier = source
                text = ''
            elif source_type == TIMEX:
                identifier = source.attrs[TID]
                text = source.attrs[VALUE]
            elif source_type == EVENT:
                identifier = source.attrs[EIID]
                text = source.attrs[FORM]
            node = Node(source, identifier, source_type, text)
            self.nodes[node.id] = node
        for n1 in self.nodes.keys():
            self.edges[n1] = {}
            for n2 in self.nodes.keys():
                self.edges[n1][n2] = Edge(n1, n2, self)

    def propagate(self, constraint):
        """Propagate the constraint through the graph, using Allen's
        constraint propagation algorithm."""
        self.cycle += 1
        if constraint.is_garbage():
            # guard against garbage constraints in the pending queue by simply
            # skipping them
            return
        self.added = []  # to keep track of what is added this cycle
        self.queue.append(constraint)
        debug(str="\n%d  %s\n" % (self.cycle, constraint))
        while self.queue:
            constraint_i_j = self.queue.pop(0)
            constraint_i_j.cycle = self.cycle
            debug(1, "POP QUEUE: %s" % (constraint_i_j))
            # compare new constraint to the one already on the edge
            edge_i_j = self.edges[constraint_i_j.node1][constraint_i_j.node2]
            (status, intersection) = self._intersect_constraints(edge_i_j,
                                                                 constraint_i_j)
            if status == 'INTERSECTION-IS-MORE-SPECIFIC':
                self.added.append(constraint_i_j)
                self._update_constraint(edge_i_j, constraint_i_j, intersection)

    def reduce(self):
        """Reduce the grap to one that does not contain any relations derived by
        closure. This does not get you a graph with the original annotations
        because some might have been removed due to inconsistencies."""
        # TODO: we may consider removing inverse relations and relations that
        # could be derived from other relations
        self.cycle += 1
        self.added = []
        self._remove_derived_relations()

    def remove_node(self, node_id):
        """Remove a node from the graph. Involves removing the node from the
        nodes hash, removing the node's column and row in the edges array and
        removing the node from edges_in and edges_out attributes of other
        nodes. This is not being used right now."""
        node = self.nodes[node_id]
        # remove from other nodes
        for node_in_id in node.edges_in.keys():
            del self.nodes[node_in_id].edges_out[node_id]
        for node_out_id in node.edges_out.keys():
            del self.nodes[node_out_id].edges_in[node_id]
        # remove from nodes hash
        del self.nodes[node_id]
        # remove from edges hash
        del self.edges[node_id]
        for other_node_id in self.edges.keys():
            del self.edges[other_node_id][node_id]

    def _update_constraint(self, edge_i_j, constraint_i_j, intersection):
        """Update a constraint by setting its relation set to the intersection
        and then add it to the edge. Once you have done that you need to check
        whether this constraint then puts further constraints on incoming edges
        to node i and outgoing edges from node j."""
        constraint_i_j.relset = intersection
        self._add_constraint_to_edge(constraint_i_j, edge_i_j)
        node_i = constraint_i_j.get_node1()
        node_j = constraint_i_j.get_node2()
        node_i.edges_out[constraint_i_j.node2] = edge_i_j
        node_j.edges_in[constraint_i_j.node1] = edge_i_j
        self._check_all_k_i_j(node_i, node_j, edge_i_j)
        self._check_all_i_j_k(node_i, node_j, edge_i_j)

    def _check_all_k_i_j(self, node_i, node_j, edge_i_j):
        """Check the constraints on [node_k --> node_i --> node_j]."""
        debug(1, "CHECKING: X --> %s --> %s" % (node_i.id, node_j.id))
        for edge_k_i in node_i.edges_in.values():
            debug(2, "%s  *  %s" % (edge_k_i, edge_i_j))
            self._check_k_i_j(edge_k_i, edge_i_j, node_i, node_j)

    def _check_all_i_j_k(self, node_i, node_j, edge_i_j):
        """Check the constriants on [node_i --> node_j --> node_k]."""
        debug(1, "CHECKING: %s --> %s --> X" % (node_i.id, node_j.id))
        for edge_j_k in node_j.edges_out.values():
            debug(2, "%s  *  %s" % (edge_i_j, edge_j_k))
            self._check_i_j_k(edge_i_j, edge_j_k, node_i, node_j)

    def _check_k_i_j(self, edge_k_i, edge_i_j, node_i, node_j):
        """Look at the k->i->j subgraph and check whether the new constraint in
        Edge(i,j) allows you to derive something new by composition. The nodes
        node_i and node_j could be derived from edge_i_j but are handed to this
        function because they were already available and it saves a bit of time
        this way."""
        node_k = edge_k_i.get_node1()
        if node_k.id == node_j.id:
            return
        edge_k_j = self._get_edge(node_k, node_j)
        relset_k_j = self._compose(edge_k_i, edge_i_j.constraint)
        debug(3, "{%s} * {%s} --> {%s}  ||  %s "
              % (edge_k_i.constraint.relset, edge_i_j.constraint.relset,
                 relset_k_j, edge_k_j.constraint))
        if relset_k_j is not None:
            self._combine(edge_k_j, relset_k_j,
                          edge_k_i.constraint, edge_i_j.constraint)

    def _check_i_j_k(self, edge_i_j, edge_j_k, node_i, node_j):
        """Look at the i->j->k subgraph and check whether the new constraint in
        Edge(i,j) allows you to derive something new by composition. The nodes
        node_i and node_j could be derived from edge_i_j but are handed to this
        function because they were already available and it saves a bit of time
        this way."""
        node_k = edge_j_k.get_node2()
        if node_k.id == node_i.id:
            return
        edge_i_k = self._get_edge(node_i, node_k)
        relset_i_k = self._compose(edge_i_j.constraint, edge_j_k)
        debug(3, "{%s} * {%s} --> {%s}  ||  %s "
              % (edge_i_j.constraint.relset, edge_j_k.constraint.relset,
                 relset_i_k, edge_i_k.constraint))
        if relset_i_k is not None:
            self._combine(edge_i_k, relset_i_k,
                          edge_i_j.constraint, edge_j_k.constraint)

    def _combine(self, edge, relset, c1, c2):
        """Compare the relation set on the edge to the relation set created by
        composition. Creates the intersection of the relation sets and checks
        the result: (i) inconsistency, (ii) more specific than relation set on
        edge, or (iii) something else. The alrgument c1 and c2 are the
        constraints that were composed to create relset and will be used to set
        the history on a new constraint if it is created."""
        edge_relset = edge.relset
        intersection = intersect_relations(edge_relset, relset)
        if intersection == '':
            debug(4, "WARNING: found an inconsistency where it shouldn't be")
            pass
        elif intersection is None:
            debug(4, "WARNING: intersection is None, this should not happen")
            pass
        elif edge_relset is None:
            self._add_constraint_to_queue(edge, intersection, c1, c2)
        elif len(intersection) < len(edge_relset):
            self._add_constraint_to_queue(edge, intersection, c1, c2)

    def _add_constraint_to_queue(self, edge, relset, c1, c2):
        new_constraint = Constraint(edge.node1, relset, edge.node2,
                                    cycle=self.cycle, source='closure',
                                    history=(c1, c2))
        self.queue.append(new_constraint)
        debug(3, "ADD QUEUE  %s " % new_constraint)
        add_inverted = False
        # Adding the inverted constraint should not be needed, except perhaps as
        # a potential minor speed increase. As far I can see however, the method
        # is actually slower when adding the inverse (about 20%), which is
        # surprising. But the results are the same.
        if add_inverted:
            relset = invert_interval_relation(relset)
            new_constraint2 = Constraint(edge.node2, relset, edge.node1,
                                         cycle=self.cycle,
                                         source='closure-inverted',
                                         history=(c1, c2))
            self.queue.append(new_constraint2)
            debug(3, "ADD QUEUE  %s " % new_constraint2)

    def _intersect_constraints(self, edge, constraint):
        """Intersect the constraint that was just derived with the one already
        on the edge. There are three cases: (1) the new constraint, if it is the
        one originally handed to the propagate() function, introduces an
        inconsistency; (2) the new constraint is identical to the one already
        there and can be ignored; (3) the intersection of the new constraint
        with the old constraint is the same as the old constraint; and (4) the
        new constraint is more specific than the already existing
        constraint. The method returns False in the first two cases and the
        intersection in the last case."""
        edge = self.edges[constraint.node1][constraint.node2]
        new_relset = constraint.relset
        existing_relset = edge.relset
        intersection = intersect_relations(new_relset, existing_relset)
        debug(2, "INTERSECT NEW {%s} WITH EXISTING {%s} --> {%s}"
              % (constraint.relset, edge.relset, intersection))
        if intersection == '':
            status = 'INCONSISTENT'
            logger.warn("Inconsistent new contraint: %s" % constraint)
            logger.warn("Clashes with: [%s] (derived from %s)"
                        % (edge.constraint, edge.constraint.history_string()))
        elif new_relset == existing_relset:
            status = 'NEW=EXISTING'
        elif intersection == existing_relset:
            status = 'INTERSECTION=EXISTING'
        else:
            status = 'INTERSECTION-IS-MORE-SPECIFIC'
        debug(2, "STATUS: %s" % status)
        return (status, intersection)

    def _compose(self, object1, object2):
        """Return the composition of the relation sets on the two objects. One
        object is an edge, the other a Constraint. Once the relations
        are retrieved from the objects all that's needed is a simple
        lookup in the compositions table."""
        rels1 = object1.relset
        rels2 = object2.relset
        return self.compositions.compose_rels(rels1, rels2)

    def _add_constraint_to_edge(self, constraint, edge):
        """This method links a constraints to its edge by retrieving the edge
        from the graph, adding the constraint to this edge, and setting the edge
        attribute on the constraint."""
        edge.add_constraint(constraint)
        constraint.edge = edge

    def _get_edge(self, node1, node2):
        """Return the edge from node1 to node2."""
        return self.edges[node1.id][node2.id]

    def get_edges(self):
        """Return all edges that have a constraint on them."""
        edges = []
        for n1 in self.edges.keys():
            for n2 in self.edges[n1].keys():
                edge = self.edges[n1][n2]
                if n1 != n2 and edge.constraint:
                    edges.append(edge)
        return edges

    def _remove_disjunctions(self):
        """Remove all disjunctions from the graph, not used now but may come in
        handy later."""
        for edge in self.get_edges():
            if edge.constraint:
                if edge.constraint.is_disjunction():
                    edge.remove_constraint()

    def _remove_derived_relations(self):
        """Remove all derived relations from the graph."""
        for edge in self.get_edges():
            if edge.is_derived():
                edge.remove_constraint()

    def _normalize_relations(self):
        """Remove all relations that are not in the set of normalized relations,
        not used now but may come in handy later."""
        for edge in self.get_edges():
            if edge.constraint:
                if not edge.constraint.has_normalized_relation():
                    edge.remove_constraint()

    def pp_nodes(self):
        """Print all nodes with their edges_in and edges_out attributes to
        standard output."""
        ids = self.nodes.keys()
        ids.sort(compare_id)
        for id in ids:
            self.nodes[id].pretty_print()

    def pp_html(self, filename=None, filehandle=None, standalone=False):
        """Print the graph to an HTML table in filename."""
        fh = open(filename, 'w') if filename else filehandle
        if standalone:
            html_graph_prefix(fh)
        fh.write("<table cellpadding=0 cellspacing=0 border=0>\n")
        fh.write("<tr><td>\n")
        nodes = self.nodes.keys()
        nodes.sort(compare_id)
        self._html_nodes_table(fh, nodes)
        fh.write("</td>\n\n")
        fh.write("<td valign=top>\n")
        self._html_added_table(fh)
        fh.write("</td></tr>\n\n")
        fh.write("</table>\n\n")
        if standalone:
            fh.write("</body>\n</html>\n\n")

    def _html_nodes_table(self, fh, nodes):
        fh.write("<table cellpadding=5 cellspacing=0 border=1>\n")
        fh.write("\n<tr>\n\n")
        fh.write("  <td>&nbsp;\n\n")
        for identifier in nodes:
            fh.write("  <td>%s\n" % identifier)
        for id1 in nodes:
            fh.write("\n\n<tr align=center>\n\n")
            fh.write("  <td align=left>%s\n" % id1)
            for id2 in nodes:
                edge = self.edges[id1][id2]
                rel = edge.relset
                if rel is None:
                    rel = '&nbsp;'
                rel = abbreviate_convex_relation(rel)
                rel = rel.replace('<', '&lt;').replace(' ', '&nbsp;')
                classes = []
                if edge.constraint:
                    classes.append(edge.constraint.source)
                    if self.cycle == edge.constraint.cycle:
                        classes.append("cycle")
                if id1 == id2:
                    classes.append("nocell")
                    # rel = '&nbsp;'
                classes = " class=\"%s\"" % ' '.join(classes)
                fh.write("  <td width=25pt%s>%s\n" % (classes, rel))
        fh.write("</table>\n\n")

    def _html_added_table(self, fh):
        fh.write("<table cellpadding=5 cellspacing=0 border=1>\n")
        if self.added:
            fh.write("<tr><td>added<td colspan=2>derived from\n")
        for c in self.added:
            fh.write("<tr>\n  <td>%s</td>\n" % c)
            if isinstance(c.history, tuple):
                fh.write("  <td>%s\n" % str(c.history[0]))
                fh.write("  <td>%s\n" % str(c.history[1]))
            elif c.history.__class__.__name__ == 'Tag':
                tlink = "TLINK(relType=%s)" % c.history.attrs.get('relType')
                fh.write("  <td colspan=2>%s\n" % tlink)
            elif c.history.__class__.__name__ == 'Constraint':
                fh.write("  <td colspan=2>%s\n" % c.history)
            else:
                fh.write("  <td colspan=2>&nbsp;\n")
        fh.write("</table>\n\n")


def debug(indent=0, str=''):
    if DEBUG:
        print '  ' * indent, str

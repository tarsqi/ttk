"""

Python wrapper around the merging code.

Calls SputLink's ConstraintPropagator do do all the work. For now does not do
any graph reduction at the end.

TODO:

- Decide what we want to take from the output. We now take all non-disjunctive
  links. We could add the disjunctive links as well. Or we could not take
  inverse relations. Or we could reduce the graph to a minimal graph.

- We now give all links, but they are not ordered. For the merging routine to be
  fully effective we should rank the TLINKs in terms of how likely they are to
  be correct.

"""

import os

from library.tarsqi_constants import LINK_MERGER
from library.main import LIBRARY
from docmodel.document import Tag
from components.common_modules.component import TarsqiComponent
from components.merging.sputlink.main import ConstraintPropagator
from components.merging.sputlink.mappings import translate_interval_relation

TTK_ROOT = os.environ['TTK_ROOT']


class MergerWrapper:

    """Wraps the merging code, including Sputlink's temporal closure code."""

    def __init__(self, document):
        self.component_name = LINK_MERGER
        self.tarsqidoc = document

    def process(self):
        """Run the contraint propagator on all TLINKS in the TarsqiDocument and
        add resulting links to the TarsqiDocument."""
        cp = ConstraintPropagator(self.tarsqidoc)
        # TODO: this is where we need to order the tlinks
        cp.queue_constraints(self.tarsqidoc.tags.find_tags(LIBRARY.timeml.TLINK))
        cp.propagate_constraints()
        cp.reduce_graph()
        self._update_tarsqidoc(cp)

    def _update_tarsqidoc(self, cp):
        """Remove existing TLINKs from the TarsqiDocument and add new ones given
        the final constraints in the graph used by the constraint propagator."""
        self.tarsqidoc.remove_tlinks()
        for n1, rest in cp.graph.edges.items():
            for n2, edge in cp.graph.edges[n1].items():
                if edge.constraint is not None:
                    if edge.constraint.has_simple_relation():
                        self._add_constraint_to_tarsqidoc(edge)

    def _add_constraint_to_tarsqidoc(self, edge):
        """Add the constraint as a TLINK to the TarsqiDocument."""
        id1 = edge.node1
        id2 = edge.node2
        origin = edge.constraint.source
        tag_or_constraints = edge.constraint.history
        attrs = {}
        if isinstance(edge.constraint.history, Tag):
            tag = edge.constraint.history
            attrs = tag.attrs
        else:
            attrs[LIBRARY.timeml.RELTYPE] = translate_interval_relation(edge.constraint.relset)
            attrs[LIBRARY.timeml.ORIGIN] = LINK_MERGER
            attrs[tlink_arg1_attr(id1)] = id1
            attrs[tlink_arg2_attr(id2)] = id2
        self.tarsqidoc.tags.add_tag(LIBRARY.timeml.TLINK, -1, -1, attrs)


def tlink_arg1_attr(identifier):
    """Return the TLINK attribute for the element linked given the identifier."""
    return _arg_attr(identifier,
                     LIBRARY.timeml.TIME_ID,
                     LIBRARY.timeml.EVENT_INSTANCE_ID)


def tlink_arg2_attr(identifier):
    """Return the TLINK attribute for the element linked given the identifier."""
    return _arg_attr(identifier,
                     LIBRARY.timeml.RELATED_TO_TIME,
                     LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE)


def _arg_attr(identifier, attr1, attr2):
    """Helper method for tlink_arg{1,2}_attr that checks the identifier."""
    return attr1 if identifier.startswith('t') else attr2

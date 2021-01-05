"""Python wrapper around the merging code.

Calls SputLink's ConstraintPropagator to do all the work. For now does not do
any graph reduction at the end.

TODO:

- Decide what we want to take from the output. We now take all non-disjunctive
  links. We could add the disjunctive links as well. Or we could not take
  inverse relations. Or we could reduce the graph to a minimal graph.

- We now put all links on the queue and order them in a rather simplistic way,
  where we have S2T < Blinker < Classifier, and classifier are ordered use the
  classifier-assigned confidence scores. For the merging routine to be better we
  should let the ranking be informed by hard evaluation data.

"""

from __future__ import absolute_import
import os

from library.tarsqi_constants import LINK_MERGER, S2T, BLINKER, CLASSIFIER
from library.main import LIBRARY
from docmodel.document import Tag
from components.common_modules.component import TarsqiComponent
from components.merging.sputlink.main import ConstraintPropagator
from components.merging.sputlink.mappings import translate_interval_relation

TTK_ROOT = os.environ['TTK_ROOT']

TLINK = LIBRARY.timeml.TLINK
LID = LIBRARY.timeml.LID
RELTYPE = LIBRARY.timeml.RELTYPE
ORIGIN = LIBRARY.timeml.ORIGIN
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
TIME_ID = LIBRARY.timeml.TIME_ID
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME


class MergerWrapper(object):

    """Wraps the merging code, including Sputlink's temporal closure code."""

    def __init__(self, document):
        self.component_name = LINK_MERGER
        self.tarsqidoc = document

    def process(self):
        """Run the contraint propagator on all TLINKS in the TarsqiDocument and
        add resulting links to the TarsqiDocument."""
        cp = ConstraintPropagator(self.tarsqidoc)
        tlinks = self.tarsqidoc.tags.find_tags(LIBRARY.timeml.TLINK)
        # order the links on how good they are
        tlinks = sorted(tlinks, key=sort_on_confidence, reverse=True)
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
        if isinstance(edge.constraint.history, Tag):
            tag = edge.constraint.history
            attrs = tag.attrs
        else:
            attrs = {
                LID: self.tarsqidoc.next_link_id(TLINK),
                RELTYPE: translate_interval_relation(edge.constraint.relset),
                ORIGIN: LINK_MERGER,
                tlink_arg1_attr(id1): id1,
                tlink_arg2_attr(id2): id2}
        self.tarsqidoc.tags.add_tag(TLINK, -1, -1, attrs)


def sort_on_confidence(link):
    """Sort key for determining how good we think a link is. Rather primitive for
    now. We consider S2T links the best, then links derived by Blinker, then
    links derived by the classifier. Classifier links themselves are ordered
    using their classifier-assigned confidence scores."""
    origin = link.attrs[ORIGIN]
    if origin.startswith(S2T):
        return 3.0
    elif origin.startswith(BLINKER):
        return 2.0
    elif origin.startswith(CLASSIFIER):
        confidence = float(origin[11:])
        return 1.0 + confidence
    else:
        return 0


def tlink_arg1_attr(identifier):
    """Return the TLINK attribute for the element linked given the identifier."""
    return _arg_attr(identifier, TIME_ID, EVENT_INSTANCE_ID)


def tlink_arg2_attr(identifier):
    """Return the TLINK attribute for the element linked given the identifier."""
    return _arg_attr(identifier, RELATED_TO_TIME, RELATED_TO_EVENT_INSTANCE)


def _arg_attr(identifier, attr1, attr2):
    """Helper method for tlink_arg{1,2}_attr that checks the identifier."""
    return attr1 if identifier.startswith('t') else attr2

"""

Python wrapper around the merging code.

Calls SputLink's ConstraintPropagator do do all the work. For now does not do
any graph reduction at the end.

TODO:

- Decide what we want to take from the output. We now take all non-disjunctive
  links. We could add the disjunctive links as well. Or we could not take
  inverse relations. or we could reduce the graph to a minimal graph.

- We now give all links, but they are not ordered. For the merging routine to be
  fully effective we should rank the TLINKs in terms of how likely they are to
  be correct.

- We now get link duplication because existing links are added again. Need to
  remove all existing links from the TarsqiDocument before we add the new batch,
  this is also needed because some of the original links may have deemed to be
  inconsistent.

- Write logger warnings when a link was not added due to inconsistencies.

"""

import os

from library.tarsqi_constants import LINK_MERGER
from library.timeMLspec import TLINK, ORIGIN, RELTYPE
from library.timeMLspec import TIME_ID, EVENT_INSTANCE_ID
from library.timeMLspec import RELATED_TO_TIME, RELATED_TO_EVENT_INSTANCE
from docmodel.document import Tag
from components.common_modules.component import TarsqiComponent
from components.merging.sputlink.main import ConstraintPropagator
from components.merging.sputlink.mappings import translate_interval_relation

TTK_ROOT = os.environ['TTK_ROOT']


class MergerWrapper:

    """Wraps the merging code, which includes Sputlinks temporal closure code."""

    def __init__(self, document):
        self.component_name = LINK_MERGER
        self.tarsqidoc = document

    def process(self):
        """Run the contraint propagator on all TLINKS in the TarsqiDocument and
        add resulting links to the TarsqiDocument."""
        cp = ConstraintPropagator(self.tarsqidoc)
        # TODO: this is where we need to order the tlinks
        cp.queue_constraints(self.tarsqidoc.tags.find_tags(TLINK))
        cp.propagate_constraints()
        # cp.reduce_graph()
        self.update_tarsqidoc(cp)

    def update_tarsqidoc(self, cp):
        self.tarsqidoc.remove_tlinks()
        for n1, rest in cp.graph.edges.items():
            for n2, edge in cp.graph.edges[n1].items():
                if edge.constraint is not None:
                    if edge.constraint.has_simple_relation():
                        self.add_edge(edge)

    def add_edge(self, edge):
        id1 = edge.node1
        id2 = edge.node2
        origin = edge.constraint.source
        tag_or_constraints = edge.constraint.history
        attrs = {}
        if isinstance(edge.constraint.history, Tag):
            tag = edge.constraint.history
            attrs = tag.attrs
        else:
            attrs[RELTYPE] = translate_interval_relation(edge.constraint.relset)
            attrs[ORIGIN] = LINK_MERGER
            if id1.startswith('t'):
                attrs[TIME_ID] = id1
            else:
                attrs[EVENT_INSTANCE_ID] = id1
            if id2.startswith('t'):
                attrs[RELATED_TO_TIME] = id2
            else:
                attrs[RELATED_TO_EVENT_INSTANCE] = id2
        self.tarsqidoc.tags.add_tag(TLINK, -1, -1, attrs)


def _get_graphfile_name(infile, identifier):
    """Return a name for a graph file in the temporary data directory, based on the
    infile name and an identifier string."""
    filename = os.path.split(infile)[-1]
    filename = "graph-%s" % os.path.splitext(filename)[-2]
    return os.path.join(TTK_ROOT, 'data', 'tmp',
                        "%s-%s.html" % (filename, identifier))

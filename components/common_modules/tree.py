"""Contains the TarsqiTree class."""

import sys
import re
from xml.sax.saxutils import escape, quoteattr

from docmodel.document import Tag
from components.common_modules.sentence import Sentence
from components.common_modules.chunks import NounChunk, VerbChunk
from components.common_modules.tokens import token_class
from components.common_modules.tags import EventTag, TimexTag
from components.common_modules.tags import AlinkTag, SlinkTag, TlinkTag
from library.main import LIBRARY
from utilities import logger


EVENT = LIBRARY.timeml.EVENT
TIMEX = LIBRARY.timeml.TIMEX
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK
EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
EVENTID = LIBRARY.timeml.EVENTID
SENTENCE = LIBRARY.timeml.SENTENCE
NOUNCHUNK = LIBRARY.timeml.NOUNCHUNK
VERBCHUNK = LIBRARY.timeml.VERBCHUNK
LEX = LIBRARY.timeml.LEX
POS = LIBRARY.timeml.POS


def create_tarsqi_tree(tarsqidoc, element, links=False):
    """Return an instance of TarsqiTree, using the tags in tarsqidoc included in
    an element, which is an Tag instance with name=docelement. Include links that
    fall within the boundaries of the elements if the optional links parameter
    is set to True."""
    # start with a Tag with just the begin and end offsets
    tree = TarsqiTree(tarsqidoc, element)
    o1 = element.begin
    o2 = element.end
    top_tag = Tag(None, o1, o2, {})
    top_node = Node(top_tag, None, tree)
    for tag in (tarsqidoc.tags.find_tags(SENTENCE, o1, o2) +
                tarsqidoc.tags.find_tags(NOUNCHUNK, o1, o2) +
                tarsqidoc.tags.find_tags(VERBCHUNK, o1, o2) +
                tarsqidoc.tags.find_tags(LEX, o1, o2) +
                tarsqidoc.tags.find_tags(EVENT, o1, o2) +
                tarsqidoc.tags.find_tags(TIMEX, o1, o2)):
        try:
            top_node.insert(tag)
        except NodeInsertionError:
            tree.orphans.append(tag)
    top_node.set_positions()
    top_node.set_event_markers()
    # recursively import all nodes into the doc, but skip the topnode itself
    top_node.add_to_tree(tree)
    if links:
        tree.initialize_alinks(tarsqidoc.tags.find_linktags(ALINK, o1, o2))
        tree.initialize_slinks(tarsqidoc.tags.find_linktags(SLINK, o1, o2))
        tree.initialize_tlinks(tarsqidoc.tags.find_linktags(TLINK, o1, o2))
    return tree


class Node(object):

    """This class is used to build a temporary hierarchical structure from instances
    of docmodel.source_parser.Tag and to turn that structure into a TarsqiTree
    instance with Sentence, NounChunk, VerbChunk, AdjectiveToken, Token,
    TimexTag and EventTag elements in the hierarchy. Nodes can be considered
    proto TarsqiTree elements or an intermediary between Tag and the classes
    like Sentence and NounChunk. Nodes know how to insert a tag into themselves
    (insert method) and how to add themselves to a TarsqiTree (add_to_tree
    method).

    Instance variables:
      name       -  the name, taken from the Tag that the Node is created from
      begin      -  the beginning offset from the Tag
      end        -  the ending offset from the Tag
      parent     -  the parent of the Node: None or another Node
      position   -  the position in the parent's dtrs list
      dtrs       -  a list of Nodes
      event_dtr  -  None or the Node from dtrs that is an event
      tag        -  the Tag that the Node is created from
      tree       -  the TarsqiTree that the Node will be inserted into as an element

    """

    # Having a higher order means that a tag x will be including tag y if x and
    # y have the same extent. Stipulates that events and times are always lower
    # in the tree than chunks.
    order = { SENTENCE: 4, NOUNCHUNK: 3, VERBCHUNK: 3,
              EVENT: 2, TIMEX: 2, LEX: 1 }

    # TODO: that stipulation is actually wrong for times and we are missing some
    # imports from GUTime because of that

    # TODO: this does not do well when there are two events at the same offsets

    def __init__(self, tag, parent, tree):
        """Initialize using a Tag object, a parent Node which can be None for the top
        node, and the TarsqiTree that the node is for."""
        self.name = tag.name
        self.begin = tag.begin
        self.end = tag.end
        self.parent = parent
        self.position = None
        self.dtrs = []
        self.event_dtr = None
        self.tag = tag
        self.tree = tree

    def __str__(self):
        attrs = ''
        if self.name == 'lex':
            lemma = self.tag.attrs.get('lemma')
            lemma = " lemma=%s" % lemma if lemma else ''
            text = ' text=' + self.tree.tarsqidoc.sourcedoc.text[self.begin:self.end]
            pos = ' pos=' + self.tag.attrs.get('pos')
            attrs = pos + lemma + text
        return "<Node %s %d-%d%s>" % (self.name, self.begin, self.end, attrs)

    def insert(self, tag):
        """Insert a Tag in the node. This could be insertion in one of the node's
        daughters, or insertion in the node's daughters list. Log a warning if
        the tag cannot be inserted."""
        # first check if tag offsets fit in self offsets
        if tag.begin < self.begin or tag.end > self.end:
            pass
        # add tag as first daughter if there are no daughters
        elif not self.dtrs:
            self.dtrs.append(Node(tag, self, self.tree))
        else:
            # find the index of the daughter that the tag would fit in and
            # insert the tag into the daughter
            idx = self._find_dtr_idx(tag)
            if idx is not None:
                self._insert_tag_into_dtr(tag, idx)
            else:
                # otherwise, find the insert point for the tag and insert it in
                # the dtrs list
                dtrs_idx = self._find_gap_idx(tag)
                if dtrs_idx is not None:
                    self.dtrs.insert(dtrs_idx, Node(tag, self, self.tree))
                else:
                    # otherwise, find the span of dtrs that the tag includes,
                    # replace the span with the tag and insert the span into the
                    # tag
                    span = self._find_span_idx(tag)
                    if span:
                        self._replace_span_with_tag(tag, span)
                    else:
                        # log warning if the tag cannot be inserted
                        # TODO: maybe downgrade to debug statement
                        logger.warn("Cannot insert %s" % tag)
                        raise NodeInsertionError

    def _insert_tag_into_dtr(self, tag, idx):
        """Insert the tag into the dtr at self.dtrs[idx]. But take care of the
        situation where the dtr and the tag have the same extent, in which case
        we need to check the specified order and perhaps replace the dtr with
        the tag and insert the dtr into the tag."""
        dtr = self.dtrs[idx]
        if dtr.begin == tag.begin and dtr.end == tag.end:
            if Node.order.get(dtr.name) > Node.order.get(tag.name):
                dtr.insert(tag)
            else:
                new_dtr = Node(tag, self, self.tree)
                new_dtr.dtrs = [dtr]
                dtr.parent = new_dtr
                self.dtrs[idx] = new_dtr
        else:
            dtr.insert(tag)

    def _replace_span_with_tag(self, tag, span):
        """Replace the span of dtrs with the tag and add the span as dtrs to the
        tag."""
        span_elements = [self.dtrs[i] for i in span]
        new_node = Node(tag, self, self.tree)
        new_node.dtrs = span_elements
        for element in span_elements:
            element.parent = new_node
        self.dtrs[span[0]:span[-1]+1] = [new_node]

    def _find_dtr_idx(self, tag):
        """Return the idex of the daughter node that can include the tag, return
        None is there is no such node."""
        for i in range(len(self.dtrs)):
            dtr = self.dtrs[i]
            if dtr.begin <= tag.begin and dtr.end >= tag.end:
                return i
        return None

    def _find_gap_idx(self, tag):
        """Return the index in the daughters list where the tag can be inserted,
        meaning that tag.begin is after the end of the previous element and that
        tag.end is before the begin of the next element. Return None if there is
        no point where the tag can be inserted."""
        for i in range(len(self.dtrs)):
            dtr = self.dtrs[i]
            # the tag fits in the gap before the dtr, we already know that the
            # tag does not overlap with previous dtrs (next case), so we can
            # return the index
            if dtr.begin >= tag.end:
                return i
            # this takes care of the case where the tag overlaps with a dtr, in
            # which case the tag does not fit in a gap
            if dtr.end > tag.begin:
                return None
        # if we fall through we can return the last offset
        return i + 1

    def _find_span_idx(self, tag):
        """Returns a list of indices of the dtrs that fit inside the tag. Returns an
        empty list if there are no dtrs that fit. Also returns an empty list if
        the begin or end of the tag is inside a dtr (this indicates a crossing
        tag, the case where the tag is inside one dtr was already dealt
        with)."""
        span = []
        for i in range(len(self.dtrs)):
            dtr = self.dtrs[i]
            # the daughter fits in the tag, append it to the span
            if dtr.begin >= tag.begin and dtr.end <= tag.end:
                span.append(i)
            # the begin or end of the tag is inside of a daughter, in that case
            # we have a crossing dependendy and don't really want this to
            # succeed
            if dtr.begin < tag.begin < dtr.end \
               or dtr.begin < tag.end < dtr.end:
                return []
        return span

    def set_positions(self):
        """For each daughter, set its position variable to its index in the
        self.dtrs list, the recurse for the daughter. These positions will later
        be handed in to the TarsqiTree elements (Sentence, VerbChunk, EventTag,
        Token etcetera)."""
        for idx in range(len(self.dtrs)):
            dtr = self.dtrs[idx]
            dtr.position = idx
            dtr.set_positions()

    def set_event_markers(self):
        """Set the self.event_dtrs variable if one of the dtrs is an event. Assumes that
        at most one daughter is an event."""
        for dtr in self.dtrs:
            if dtr.name == 'EVENT':
                self.event_dtr = dtr
            dtr.set_event_markers()

    def add_to_tree(self, tree_element):
        """Add all daughters in self.dtrs as tree_elements to the initially
        empty list in tree_element.dtrs. Add them as instances of Sentence,
        NounChunk, VerbChunk, EventTag, TimexTag, Token or AdjectiveToken. The
        tree_element argument can be one of those seven elements or it can be a
        TarsqiTree."""
        for dtr in self.dtrs:
            tree_element_dtr = dtr.as_tree_element()
            tree_element_dtr.parent = tree_element
            if tree_element_dtr.isAdjToken() and tree_element.isEvent():
                tree_element_dtr.event = True
                tree_element_dtr.event_tag = tree_element
            tree_element.dtrs.append(tree_element_dtr)
            dtr.add_to_tree(tree_element_dtr)

    def as_tree_element(self):
        """Create from the node an instance of Sentence, NounChunk, VerbChunk,
        EventTag, TimexTag, Token or AdjectiveToken. Copy information from the
        Node as needed."""
        if self.name == SENTENCE:
            tree_element = Sentence()
        elif self.name == NOUNCHUNK:
            tree_element = NounChunk()
        elif self.name == VERBCHUNK:
            tree_element = VerbChunk()
        elif self.name == LEX:
            pos = self.tag.attrs[POS]
            word = self.tree.tarsqidoc.sourcedoc[self.begin:self.end]
            tree_element = token_class(pos)(word, pos)
        elif self.name == EVENT:
            tree_element = EventTag(self.tag.attrs)
        elif self.name == TIMEX:
            tree_element = TimexTag(self.tag.attrs)
        if self.event_dtr is not None:
            tree_element.event = True
            tree_element.eid = self.event_dtr.tag.attrs['eid']
            tree_element.eiid = self.event_dtr.tag.attrs['eiid']
        # inherit some goodies from the Node
        tree_element.position = self.position
        tree_element.tree = self.tree
        tree_element.begin = self.begin
        tree_element.end = self.end
        tree_element.tag = self.tag
        return tree_element

    def pp(self, indent=0):
        print "%s%s" % (indent * '  ', self)
        for dtr in self.dtrs:
            dtr.pp(indent + 1)


class NodeInsertionError(Exception):

    """An exception used to trap cases where you insert a node in the tree and there
    is no place where it can go."""


class TarsqiTree:

    """Implements the shallow tree that is input to some of the Tarsqi components.

    Instance variables
        tarsqidoc   -  the TarsqiDocument instance that the tree is part of
        docelement  -  the Tag with name=docelement that the tree was made for
        parent      -  the parent of the tree, which is always None
        dtrs        -  a list with daughters
        events      -  a dictionary with events found by Evita
        alinks      -  a list of AlinkTags, filled in by Slinket
        slinks      -  a list of SlinkTags, filled in by Slinket
        tlinks      -  a list of TlinkTags
        orphans     -  a list of tags that could not be inserted

    The events dictionary is used by Slinket and stores events from the tree
    indexed on event eids."""

    def __init__(self, tarsqidoc, docelement_tag):
        """Initialize all dictionaries, list and counters and set the file
        name."""
        self.tarsqidoc = tarsqidoc
        self.docelement = docelement_tag
        self.parent = None
        self.dtrs = []
        self.events = {}
        self.alinks = []
        self.slinks = []
        self.tlinks = []
        self.orphans = []

    def __len__(self):
        """Length is determined by the length of the dtrs list."""
        return len(self.dtrs)

    def __getitem__(self, index):
        """Indexing occurs on the dtrs variable."""
        return self.dtrs[index]

    def get_nodes(self):
        """Returns a list of all nodes in the tree."""
        nodes = []
        for dtr in self.dtrs:
            nodes.extend(dtr.all_nodes())
        return nodes

    def get_sentences(self):
        """Returns a list of all sentences in the tree."""
        return [s for s in self.dtrs if s.isSentence()]

    def initialize_alinks(self, alinks):
        for alink in alinks:
            self.alinks.append(AlinkTag(alink.attrs))

    def initialize_slinks(self, slinks):
        for slink in slinks:
            self.slinks.append(SlinkTag(slink.attrs))

    def initialize_tlinks(self, tlinks):
        for tlink in tlinks:
            self.tlinks.append(TlinkTag(tlink.attrs))

    def hasEventWithAttribute(self, eid, att):
        """Returns the attribute value if the events dictionary has an event
        with the given id that has a value for the given attribute, returns
        False otherwise. Arguments:
           eid - a string indicating the eid of the event
           att - a string indicating the attribute"""
        return self.events.get(eid, {}).get(att, False)

    def storeEventValues(self, pairs):
        """Store attributes associated with an event (that is, they live on an event or
        makeinstance tag) in the events dictionary. The pairs argument is a
        dcitionary of attributes"""
        # get eid from event or instance
        try:
            eid = pairs[EID]
        except KeyError:
            eid = pairs[EVENTID]
        # initialize dictionary if it is not there yet
        if eid not in self.events:
            self.events[eid] = {}
        # add data
        for (att, val) in pairs.items():
            self.events[eid][att] = val

    def addEvent(self, event):
        """Takes an instance of evita.event.Event and adds it to the
        TagRepository on the TarsqiDocument. Does not add it if there is already
        an event at the same location."""
        # NOTE: we now always have one token on this list, if there are more in
        # a future implementation we takes the last, but what probably should
        # happen is that we take the begin offset from the first and the end
        # offset from the last token.
        token = event.tokens[-1]
        if self.tarsqidoc.has_event(token.begin, token.end):
            logger.warn("There already is an event at that location.")
        else:
            event_attrs = dict(event.attrs)
            # with the current implementation, there is always one instance per
            # event, so we just reuse the event identifier for the instance
            eid = self.tarsqidoc.next_event_id()
            eiid = "ei%s" % eid[1:]
            event_attrs['eid'] = eid
            event_attrs['eiid'] = eiid
            # TODO: at least the second test does not seem needed anymore
            event_attrs = { k: v for k, v in event_attrs.items()
                            if v is not None and k is not 'eventID' }
            self.tarsqidoc.add_event(token.begin, token.end, event_attrs)

    def addLink(self, linkAttrs, linkType):
        """Add a link of type linkType with its attributes to the tree by appending
        them to self.alink_list, self.slink_list or self.tlink_list. This allows
        other code, for example the main function of Slinket, to easily access
        newly created links in the TarsqiTree. The linkType argument is'ALINK',
        'SLINK' or 'TLINK' and linkAttrs is a dictionary of attributes."""
        linkAttrs['lid'] = self.tarsqidoc.next_link_id(linkType)
        if linkType == ALINK:
            self.alinks.append(AlinkTag(linkAttrs))
        elif linkType == SLINK:
            self.slinks.append(SlinkTag(linkAttrs))
        elif linkType == TLINK:
            self.tlinks.append(TlinkTag(linkAttrs))

    def pp(self):
        """Short form of pretty_print()"""
        self.pretty_print()

    def pretty_print(self):
        """Pretty printer that prints all instance variables and a neat representation
        of the sentences."""
        print "\n<TarsqiTree filename=%s>\n" % self.tarsqidoc.sourcedoc.filename
        print "len(dtrs) = %s" % (len(self.dtrs))
        self.pretty_print_tagged_events_dict()
        self.pretty_print_sentences()
        self.pretty_print_links(self.alinks)
        self.pretty_print_links(self.slinks)
        self.pretty_print_links(self.tlinks)

    def pretty_print_tagged_events_dict(self):
        print 'events = {',
        eids = sorted(self.events.keys())
        for eid in eids:
            print "\n   ", eid, '=> {',
            attrs = self.events[eid].keys()
            attrs.sort()
            for attr in attrs:
                print "%s=%s" % (attr, str(self.events[eid][attr])),
            print '}'
        print '}'

    def pretty_print_sentences(self):
        for sentence in self:
            print
            sentence.pretty_print(verbose=False)
        print

    def pretty_print_links(self, links):
        for link in links:
            print ' ', link

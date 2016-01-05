"""Contains the TarsqiTree class."""

import sys
import re
from xml.sax.saxutils import escape, quoteattr

from components.common_modules.sentence import Sentence
from components.common_modules.chunks import NounChunk, VerbChunk
from components.common_modules.tokens import Token, AdjectiveToken
from components.common_modules.tags import EventTag, InstanceTag, TimexTag
from components.common_modules.tags import AlinkTag, SlinkTag, TlinkTag
from library.timeMLspec import EID, EIID, EVENTID
from library.timeMLspec import ALINK, SLINK, TLINK
from library.timeMLspec import POS_ADJ


def create_tarsqi_tree(element):
    """Return an instance of TarsqiTree, using the tags in element, which is an
    instance of TarsqiDocElement or a subclass."""
    top_node = Node(begin=element.begin, end=element.end)
    for tag in (element.tarsqi_tags.find_tags('s') +
                element.tarsqi_tags.find_tags('NG') +
                element.tarsqi_tags.find_tags('VG') +
                element.tarsqi_tags.find_tags('lex') +
                element.tarsqi_tags.find_tags('EVENT') +
                element.tarsqi_tags.find_tags('TIMEX3')):
        top_node.insert(tag)
    top_node.set_positions()
    top_node.set_event_markers()
    tree = TarsqiTree(element.doc, element)
    # recursively import all nodes into the doc, but skip the topnode itself
    top_node.add_to_doc(tree, tree)
    return tree


class Node(object):

    """This class is used to build a temporary hierarchical structure from instances
    of docmodel.source_parser.Tag. It is also used to turn that structure into a
    TarsqiTree instance, with Sentence, NounChunk, VerbChunk, AdjectiveToken,
    Token, TimexTag and EventTag elements in the hierarchy."""

    # Having a higher order means that a tag x will be including tag y if x and
    # y have the same extent.
    order = { 'TarsqiTree': 5, 's': 4, 'NG': 3,'VG': 3, 'EVENT': 2, 'TIMEX3': 2, 'lex': 1 }

    def __init__(self, tag=None, name='TarsqiTree', parent=None, begin=None, end=None):
        self.name = name
        self.document = None
        self.parent = parent
        self.position = None     # position in the parent's dtr list
        self.dtrs = []
        self.event_dtr = None
        self.begin = begin
        self.end = end
        self.tag = tag
        if tag is not None:
            self.begin = tag.begin
            self.end = tag.end
            self.name = tag.name

    def __str__(self):
        lemma = ''
        if self.tag is not None and self.tag.attrs.has_key('lemma'):
            lemma = ' "' + self.tag.attrs['lemma'] + '"'
        return "<Node %s %d-%d%s>" % (self.name, self.begin, self.end, lemma)

    def insert(self, tag):
        """Insert a tag in the node. This could be insertion in one of the node's
        daughters, or insertion in the node's daughters list. Print a warning if
        the tag cannot be inserted."""
        # first check if tag offsets fit in self offsets
        if tag.begin < self.begin or tag.end > self.end:
            print "WARNING: cannot insert tag because " \
                + "its boundaries are outside of the nodes boundaries"
        # add tag as first daughter if there are no daughters
        elif not self.dtrs:
            self.dtrs.append(Node(tag, parent=self))
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
                    self.dtrs.insert(dtrs_idx, Node(tag, parent=self))
                else:
                    # otherwise, find the span of dtrs that the tag includes,
                    # replace the span with the tag and insert the span into the
                    # tag
                    span = self._find_span_idx(tag)
                    if span:
                        self._replace_span_with_tag(tag, span)
                    else:
                        # print warning if the tag cannot be inserted
                        print "WARNING: cannot insert tag because it overlaps with other tags."

    def _insert_tag_into_dtr(self, tag, idx):
        """Insert the tag into the dtr at self.dtrs[idx]. But take care of the situation
        where the dtr and the tag have the same extent, in which case we need to
        check the specified order and perhaps replace the dtr with the tag and
        insert the dtr into the tag."""
        dtr = self.dtrs[idx]
        if dtr.begin == tag.begin and dtr.end == tag.end:
            if Node.order.get(dtr.name) > Node.order.get(tag.name):
                dtr.insert(tag)
            else:
                new_dtr = Node(tag, parent=self)
                new_dtr.dtrs = [dtr]
                dtr.parent = new_dtr
                self.dtrs[idx] = new_dtr
        else:
            dtr.insert(tag)

    def _replace_span_with_tag(self, tag, span):
        """Replace the span of dtrs with the tag and add the span as dtrs to the tag."""
        span_elements = [self.dtrs[i] for i in span]
        new_node = Node(tag, parent=self)
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
        """Set the self.event_dtrs variable if one of the dtrs is an event."""
        # NOTE: this is problematic if there is more than one event
        for dtr in self.dtrs:
            self.event_dtr = dtr if dtr.name == 'EVENT' else None
            dtr.set_event_markers()

    def add_to_doc(self, doc_element, tree):
        for dtr in self.dtrs:
            doc_element_dtr = dtr.as_doc_element(tree)
            doc_element_dtr.parent = doc_element
            if doc_element_dtr.isAdjToken() and doc_element.isEvent():
                doc_element_dtr.event = True
                doc_element_dtr.event_tag = doc_element
            doc_element.dtrs.append(doc_element_dtr)
            dtr.add_to_doc(doc_element_dtr, tree)

    def as_doc_element(self, tree):
        """Create from the node an instance of Sentence, NounChunk, VerbChunk, EventTag,
        TimexTag, Token or AdjectiveToken."""
        if self.name == 's':
            doc_element = Sentence()
        elif self.name == 'NG':
            doc_element = NounChunk('NG')
        elif self.name == 'VG':
            doc_element = VerbChunk('VG')
        elif self.name == 'lex':
            pos = self.tag.attrs['pos']
            word = tree.tarsqidoc.source[self.begin:self.end]
            token_class = AdjectiveToken if pos.startswith(POS_ADJ) else Token
            doc_element = token_class(tree, word, pos)
        elif self.name == 'EVENT':
            doc_element = EventTag(self.tag.attrs)
        elif self.name == 'TIMEX3':
            doc_element = TimexTag(self.tag.attrs)
        doc_element.position = self.position
        if self.event_dtr is not None:
            doc_element.event = 1
            doc_element.eid = self.event_dtr.tag.attrs['eid']
            doc_element.eiid = self.event_dtr.tag.attrs['eiid']
        doc_element.begin = self.begin
        doc_element.end = self.end
        return doc_element

    def pp(self, indent=0):
        print "%s%s" % (indent * '  ', self)
        for dtr in self.dtrs:
            dtr.pp(indent + 1)



class TarsqiTree:

    """Implements the shallow tree that is input to some of the Tarsqi components.

    Instance variables
        tarsqidoc     -  the TarsqiDocument instance that the tree is part of
        docelement    -  the TarsqiDocElement that the tree was made for
        events        -  a dictionary with events found by Evita
        alink_list    -  a list of AlinkTags, filled in by Slinket
        slink_list    -  a list of SlinkTags, filled in by Slinket
        tlink_list    -  a list of TlinkTags

    The events dictionary is used by Slinket and stores events from the tree
    indexed on event eids."""

    def __init__(self, tarsqidoc=None, tarsqidocelement=None):
        """Initialize all dictionaries, list and counters and set the file name."""
        self.tarsqidoc = tarsqidoc
        self.docelement = tarsqidocelement
        self.dtrs = []
        self.events = {}
        self.alink_list = []
        self.slink_list = []
        self.tlink_list = []

    def __len__(self):
        """Length is determined by the length of the dtrs list."""
        return len(self.dtrs)

    def __getitem__(self, index):
        """Indexing occurs on the dtrs variable."""
        return self.dtrs[index]

    def addSentence(self, sentence):
        """Append a Sentence to the dtrs list and sets the parent feature of the
        sentence to the tree."""
        sentence.setParent(self)
        self.dtrs.append(sentence)

    def addTimex(self, timex):
        """Applied when a timex cannot be added to a Chunk or a Sentence, probably
        intended for the DCT."""
        # NOTE: this is probably wrong, test it with a document where
        # the DCT will not end up in a sentence tag
        timex.setParent(self)
    
    def hasEventWithAttribute(self, eid, att):
        """Returns the attribute value if the events dictionary has an event with the given
        id that has a value for the given attribute, returns False otherwise
        Arguments
           eid - a string indicating the eid of the event
           att - a string indicating the attribute"""
        return self.events.get(eid,{}).get(att,False)

    def storeEventValues(self, pairs):
        """Store attributes associated with an event (that is, they live on an event or
        makeinstance tag) in the events dictionary. The pairs argument is a
        dcitionary of attributes"""
        # get eid from event or instance
        try: eid = pairs[EID]
        except KeyError: eid = pairs[EVENTID]
        # initialize dictionary if it is not there yet
        if not eid in self.events:
            self.events[eid] = {}
        # add data
        for (att, val) in pairs.items():
            self.events[eid][att] = val

    def tree(self):
        """Returns the tree itself. This is so that chunks can ask their parent for
        the tree without having to worry whether the parent is a Sentence or a
        TarsqiTree."""
        return self

    def addEvent(self, event):
        """Takes an instance of evita.event.Event and adds it to the tagrepository on
        the TarsqiDocElement."""
        # TODO: this combines the information from the event and the instance
        # and it is here because of the legacy difference between events and
        # instances, at some point event and instance will be merged
        event_attrs = dict(event.attrs)
        event_attrs.update(event.instanceList[0].attrs)
        # with the current implementation, there is always one instance per
        # event, so we just reuse the event identifier for the instance
        eid = self.tarsqidoc.next_event_id()
        eiid = "ei%s" % eid[1:]
        event_attrs['eid'] = eid
        event_attrs['eiid'] = eiid
        event_attrs = { k:v for k,v in event_attrs.items()
                        if v is not None and k is not 'eventID' }
        # TODO: this assumes the event is always the last one, which may not
        # always be true
        token = event.tokenList[-1]
        self.docelement.add_event(token.begin, token.end, event_attrs)
        
    def addLink(self, linkAttrs, linkType):
        """Add a link of type linkType with its attributes to the tree by appending
        them to self.alink_list, self.slink_list or self.tlink_list. This allows
        other code, for example the main function of Slinket, to easily access
        newly created links in the TarsqiTree. The linkType argument is'ALINK',
        'SLINK' or 'TLINK' and linkAttrs is a dictionary of attributes."""
        linkAttrs['lid'] = self.tarsqidoc.next_link_id(linkType)
        if linkType == ALINK: self.alink_list.append(AlinkTag(linkAttrs))
        elif linkType == SLINK: self.slink_list.append(SlinkTag(linkAttrs))
        elif linkType == TLINK: self.tlink_list.append(TlinkTag(linkAttrs))

    def pp(self):
        """Short form of pretty_print()"""
        self.pretty_print()

    def pretty_print(self):
        """Pretty printer that prints all instance variables and a neat representation of
        the sentences."""
        print "\n<TarsqiTree filename=%s>\n" % self.tarsqidoc.source.filename
        print "  len(dtrs)=%s" % (len(self.dtrs))
        self.pretty_print_tagged_events_dict()
        print '  alink_list =', self.alink_list
        print '  slink_list =', self.slink_list
        print '  tlink_list =', self.tlink_list
        self.pretty_print_sentences()

    def pretty_print_tagged_events_dict(self):
        print '  events'
        eids = sorted(self.events.keys())
        for eid in eids:
            print '   ', eid, '=> {',
            attrs = self.events[eid].keys()
            attrs.sort()
            for attr in attrs:
                print "%s=%s" % (attr, str(self.events[eid][attr])),
            print '}'

    def pretty_print_sentences(self):
        count = 0
        for sentence in self:
            count = count + 1
            print "\nSENTENCE " + str(count) + "\n"
            sentence.pretty_print()
        print "\n"


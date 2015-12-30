"""Contains functionality specific to documents."""

import sys
import re
from xml.sax.saxutils import escape, quoteattr

from utilities.xml_utils import emptyContentString
from components.common_modules.sentence import Sentence
from components.common_modules.chunks import NounChunk, VerbChunk
from components.common_modules.tokens import Token, AdjectiveToken
from components.common_modules.tags import EventTag, InstanceTag, TimexTag
from components.common_modules.tags import AlinkTag, SlinkTag, TlinkTag
from library.timeMLspec import EID, EIID, EVENTID
from library.timeMLspec import ALINK, SLINK, TLINK
from library.timeMLspec import POS_ADJ


def create_document_from_tarsqi_doc_element(element):
    """Return an instance of Document, using the tags in element, which is an
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
    # TODO: merge 2nd and 3rd arguments?
    doc = Document(element.doc.source.filename, element.doc, element)
    top_node.add_to_doc(doc, doc)
    doc.sentenceList = doc.dtrs
    #top_node.pp()
    #doc.pp()
    return doc


class Node(object):

    """This class is used to build a temporary hierarchical structure from instances
    of docmodel.source_parser.Tag. It is also used to turn that structure into a
    Document instance, with Sentence, NounChunk, VerbChunk, AdjectiveToken,
    Token, TimexTag and EventTag elements in the hierarchy."""

    # Having a higher order means that a tag x will be including tag y if x and
    # y have the same extent.
    order = { 'Document': 5, 's': 4, 'NG': 3,'VG': 3, 'EVENT': 2, 'TIMEX3': 2, 'lex': 1 }

    def __init__(self, tag=None, name='Document', parent=None, begin=None, end=None):
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
        be handed in to the Document elements (Sentence, VerbChunk, EventTag,
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

    def add_to_doc(self, doc_element, document):
        for dtr in self.dtrs:
            doc_element_dtr = dtr.as_doc_element(document)
            doc_element_dtr.parent = doc_element
            if doc_element_dtr.isAdjToken() and doc_element.isEvent():
                doc_element_dtr.event = True
                doc_element_dtr.event_tag = doc_element
            doc_element.dtrs.append(doc_element_dtr)
            dtr.add_to_doc(doc_element_dtr, document)

    def as_doc_element(self, document):
        """Create an instance of Sentence, NounChunk, VerbChunk, EventTag,
        TimexTag, Token or AdjectiveToken."""
        if self.name == 's':
            doc_element = Sentence()
        elif self.name == 'NG':
            doc_element = NounChunk('NG')
        elif self.name == 'VG':
            doc_element = VerbChunk('VG')
        elif self.name == 'lex':
            pos = self.tag.attrs['pos']
            word = document.tarsqidoc.source[self.begin:self.end]
            if pos.startswith(POS_ADJ):
                doc_element = AdjectiveToken(document, pos)
            else:
                doc_element = Token(document, pos)
            doc_element.text = word
        elif self.name == 'EVENT':
            doc_element = EventTag(self.tag.attrs)
        elif self.name == 'TIMEX3':
            doc_element = TimexTag(self.tag.attrs)
        doc_element.position = self.position
        if self.event_dtr is not None:
            doc_element.event = 1
            doc_element.eid = self.event_dtr.tag.attrs['eid']
            doc_element.eiid = self.event_dtr.tag.attrs['eiid']
        return doc_element

    def pp(self, indent=0):
        print "%s%s" % (indent * '  ', self)
        for dtr in self.dtrs:
            dtr.pp(indent + 1)



class Document:

    """Implements the shallow tree that is input to some of the Tarsqi components.

    Instance variables

        tarsqidoc - the TarsqiDocument instance that the document is part of
                    (this is the link back to the SourceDoc with the text)
        tarsqidocelement

        nodeList - a list of strings, each representing a document element
        sentenceList - a list of Sentences
        nodeCounter - an integer
        sourceFileName  an absolute path
        taggedEventsDict - a dictionary containing tagged event in the input
        instanceCounter - an integer
        insertDict - dictionary (integer --> string)

        event_dict - dictionary (eid --> EventTag)
        instance_dict a dictionary (eiid --> InstanceTag)
        alink_list - a list of AlinkTags
        slink_list - a list of SlinkTags
        tlink_list - a list of TlinkTags

        eventCount - an integer
        alinkCount - an integer
        slinkCount - an integer
        tlinkCount - an integer
        linkCount - an integer
        positionCount - an integer

    The taggedEventsDicts is used by Slinket, storing events indexed on event IDs, its
    function can probably be taken over by the event_dict variable. The insertDict
    variable is used by Evita. It keeps track of event and instance tags that need to be
    inserted and indexes them on the index in the nodeList where they need to be inserted.

    The variables event_dict, instance_dict, alink_list, slink_list and tlink_list are
    filled in by the FragmentConverter.

    The counters are incremented when elements are added, most counters are used to create
    unique ids for newly created tags. The positionCount is incremented when a sentence or
    a timex is added to the document (using addSentence or addTimex). It is used so the
    position variable can be set on Sentences (that is, the Sentence knows at what
    position in the document it occurrs)."""


    def __init__(self, fileName, tarsqidoc=None, tarsqidocelement=None):
        """Initialize all dictionaries, list and counters and set the file name."""
        self.tarsqidoc = tarsqidoc
        self.tarsqidocelement = tarsqidocelement
        self.nodeList = []
        self.sentenceList = []
        self.dtrs = []                    # used intially as stand in for sentenceList by Node
        self.nodeCounter = 0
        self.sourceFileName = fileName
        self.taggedEventsDict = {}        # used by slinket's event parser
        self.instanceCounter = 0
        self.insertDict = {}              # filled in by Evita
        self.event_dict = {}              # next five created by the FragmentConverter
        self.instance_dict = {}
        self.alink_list = []
        self.slink_list = []
        self.tlink_list = []
        self.eventCount = 0
        self.alinkCount = 0
        self.slinkCount = 0 
        self.tlinkCount = 0 
        self.linkCount = 1                # used by S2T
        self.positionCount = 0            # obsolete?

    def __len__(self):
        """Length is determined by the length of the sentenceList."""
        return len(self.sentenceList)

    def __getitem__(self, index):
        """Indexing occurs on the sentenceList variable."""
        return self.sentenceList[index]

    def addDocNode(self, string):
        """Add a node to the document's nodeList. Inserts it at the location
        indicated by the nodeCounter.
        Arguments
           string - a string representing a tag or text"""
        # could probably add it by appending it to nodeList
        self.nodeList.insert(self.nodeCounter, string)
        self.nodeCounter = self.nodeCounter + 1 

    def addDocLink(self, loc, string):
        """Add a node to the document's nodeList. Inserts it at the specified location and
        not at the ned of the document (as indicated by noedeCounter. Still increments the
        nodeCounter becasue the document grows by one element. This is much like
        addDocNode, but it used for adding nodes that were not in the input but that were
        created by a Tarsqi component.
        Arguments
           loc - an integer, iundicating the location of the insert point
           string - a string representing a tag or text"""
        self.nodeList.insert(loc, string)
        self.nodeCounter = self.nodeCounter + 1
                
    def addSentence(self, sentence):
        """Append a Sentence to the sentenceList and sets the parent feature of the
        sentence to the document. Also increments the positionCount."""
        sentence.setParent(self)
        self.sentenceList.append(sentence)
        self.positionCount += 1

    def addTimex(self, timex):
        """Applied when a timex cannot be added to a Chunk or a Sentence, probably
        intended for the DCT."""
        # NOTE: this is probably wrong, test it with a document where
        # the DCT will not end up in a sentence tag
        timex.setParent(self)
        self.positionCount += 1
    
    def hasEventWithAttribute(self, eid, att):
        """Returns the attribute value if the taggedEventsDict has an event with the given
        id that has a value for the given attribute, returns False otherwise
        Arguments
           eid - a string indicating the eid of the event
           att - a string indicating the attribute"""
        return self.taggedEventsDict.get(eid,{}).get(att,False)

    def storeEventValues(self, pairs):
        """Store attributes associated with an event (that is, they live on an event or
        makeinstance tag) in the taggedEventsDictionary. The pairs argument is a
        dcitionary of attributes"""
        # get eid from event or instance
        try: eid = pairs[EID]
        except KeyError: eid = pairs[EVENTID]
        # initialize dictionary if it is not there yet
        if not eid in self.taggedEventsDict:
            self.taggedEventsDict[eid] = {}
        # add data
        for (att, val) in pairs.items():
            self.taggedEventsDict[eid][att] = val

    def document(self):
        """Returns the document itself. This is so that chunks can ask their parent for
        the document without having to worry whether the parent is a Sentence or a
        Document."""
        return self

    def addEvent(self, event):
        """Adds an Event to the XML document."""
        # with the current implementation, there is always one instance per
        # event, so we just reuse the eventID for theinstanceID.
        # TODO: delete this once we update the TarsqiDocElement directly
        eventID = self.tarsqidoc.next_event_id()
        instanceID = "ei%s" % eventID[1:]
        event.attrs["eid"] = eventID 
        for instance in event.instanceList:
            instance.attrs["eiid"] = instanceID
            instance.attrs["eventID"] = eventID
        event.addToXmlDoc()

        
    def addLink(self, linkAttrs, linkType):

        """Add an Alink or Slink to the document. Adds it at the end of the document, that
        is, at the position indicated by the instance variable nodeCount. This means that
        the resulting file is not valid XML, but this is not problematic since the file is
        a fragment that is inserted back into the whole file. This will break down though
        is the fragment happens to be the outermost tag of the input file. This method
        should probably use addDocLink instead of addDocNode.

        Also adds alinks, slinks and tlinks to the link lists. This is to make sure that
        for example the main function of Slinket can easily access newly created links in
        the Document and insert them in the XmlDocument.
        
        Note that TLinks are added directly to the xml document and not to the
        Document. Evita and Slinket are not yet updated to add to the xmldoc and hence
        need this method.

        Arguments
           linkAttrs - dictionary of attributes
           linkType - 'ALINK' | 'SLINK' """

        linkAttrs['lid'] = self._getNextLinkID(linkType)
        self.addDocNode(emptyContentString(linkType, linkAttrs))

        if linkType == ALINK:
            self.alink_list.append(AlinkTag(linkAttrs))
        elif linkType == SLINK:
            self.slink_list.append(SlinkTag(linkAttrs))
        elif linkType == TLINK:
            self.tlink_list.append(TlinkTag(linkAttrs))


    def get_events(self, result=None):
        # TODO: this is also defined on Sentence and Document
        if result is None:
            result = []
        for dtr in self.dtrs:
            if dtr.isEvent():
                result.append(dtr)
            dtr.get_events(result)
        return result

    def _getNextTimexID(self):
        tids = []
        re_tid = re.compile('tid="t(\d+)"')
        for node in self.nodeList:
            if node.startswith('<TIMEX3'):
                match = re_tid.search(node)
                if match:
                    id = match.group(1)
                    tids.append(int(id))
        tids.sort()
        try:
            next_id = tids[-1] + 1
        except IndexError:
            next_id = 1
        return "t%d" % next_id

    def _getNextLinkID(self, linkType):
        """Return a unique lid. The linkType argument is one of {ALINK,SLINK,TLINK} and
        has no influence over the lid that is returned but determines what link counter is
        incremented. Assumes that all links are added using the link counters in the
        document. Breaks down if there are already links added without using those
        counters. """
        # TODO: move this to TarsqiDocument
        if linkType == ALINK:
            return self._getNextAlinkID()
        elif linkType == SLINK:
            return self._getNextSlinkID()
        elif linkType == TLINK:
            return self._getNextSlinkID()
        else:
            logger.error("Could not create link ID for link type" + str(linkType))

    def _getNextAlinkID(self):
        """Increment alinkCount and return a new unique lid."""
        # TODO: move this to TarsqiDocument
        self.alinkCount += 1
        return "l"+str(self.alinkCount + self.slinkCount + self.tlinkCount)
    
    def _getNextSlinkID(self):
        """Increment slinkCount and return a new unique lid."""
        # TODO: move this to TarsqiDocument
        self.slinkCount += 1
        return "l"+str(self.alinkCount + self.slinkCount + self.tlinkCount)

    def _getNextTlinkID(self):
        """Increment tlinkCount and return a new unique lid."""
        # TODO: move this to TarsqiDocument
        self.tlinkCount += 1
        return "l"+str(self.alinkCount + self.slinkCount + self.tlinkCount)

    def pp(self):
        """Short form of pretty_print()"""
        self.pretty_print()

    def pretty_print(self):
        """Pretty printer that prints all instance variables and a neat representation of
        the sentence list."""
        print "\n<Document sourceFilename=%s>\n" % self.sourceFileName
        print "  len(nodeList)=%s len(sentenceList)=%s" \
            % (len(self.nodeList), len(self.sentenceList))
        print "  nodeCounter=%s instanceCounter=%s eventCount=%s postionCount=%s" \
            % (self.nodeCounter, self.instanceCounter, self.eventCount, self.positionCount)
        print "  alinkCount=%s slinkCount=%s tlinkCount=%s" \
            % (self.alinkCount, self.slinkCount, self.tlinkCount)
        self.pretty_print_tagged_events_dict()
        print '  insertDict =', self.insertDict
        print "  len(event_dict)=%s len(instance_dict)=%s" \
            % (len(self.event_dict), len(self.instance_dict))
        print '  alink_list =', self.alink_list
        print '  slink_list =', self.slink_list
        print '  tlink_list =', self.tlink_list
        self.pretty_print_sentences()

    def pretty_print_tagged_events_dict(self):
        print '  taggedEventsDict'
        eids = sorted(self.taggedEventsDict.keys())
        for eid in eids:
            print '   ', eid, '=> {',
            attrs = self.taggedEventsDict[eid].keys()
            attrs.sort()
            for attr in attrs:
                print "%s=%s" % (attr, str(self.taggedEventsDict[eid][attr])),
            print '}'

    def pretty_print_sentences(self):
        count = 0
        for sentence in self.sentenceList:
            count = count + 1
            print "\nSENTENCE " + str(count) + "\n"
            sentence.pretty_print()
        print "\n"


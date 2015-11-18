"""Contains converters that map between representations.

Currently contains two converters. ChunkerOutrputConverter takes the
one-sentence-per-line output of the chunker and adds lex tags and s
tags. FragmentConverter takes an XmlDocument and creates an instance
of the Document class.

"""

import time
from types import StringType, FileType

from components.common_modules.document import Document
from components.common_modules.sentence import Sentence
from components.common_modules.chunks import NounChunk, VerbChunk
from components.common_modules.tokens import Token, AdjectiveToken
from components.common_modules.tags import EventTag, InstanceTag, TimexTag
from components.common_modules.tags import AlinkTag, SlinkTag, TlinkTag

from library.timeMLspec import SENTENCE, NOUNCHUNK, VERBCHUNK, TOKEN
from library.timeMLspec import EVENT, INSTANCE, TIMEX, ALINK, SLINK, TLINK
from library.timeMLspec import LID, EID, EIID, EVENTID
from library.timeMLspec import POS, POS_ADJ, FORM, EPOS
from utilities import logger


class Converter:

    """New Converter class to take the place of FragmentConverter. It
    takes an XmldDocument and creates a Document, using a much simpler
    approach than the one in FragmentConverter. This should probably
    be implemented in document.py as a class named DocumentCreator or
    perhaps on Document itself.

    However, before all this happens some things must be in place:

    Test cases for Evita and Slinket (the two consumers of Converter)
    
    Token and AdjectiveToken redesign:
    - __init__ takes doc and the xmldocelement (the lex, and therefore
      also lid, pos, lemma)
    - getText does not go to the doc.nodeList

    All Constituents have a method add_child, which appends to the
    dtrs list (or whatever variable they have).

    Check whether links need to be accounted for. FragmentConverter
    deals with those but perhaps only because of S2T.  """

    
    def __init__(self, xmldoc, filename=None):

        """Initializes xmldoc and doc, using two arguments: xmldoc (an
        XmlDocument) and filename (a string). Also sets instance
        variables currentSentence, currentChunk, currentToken,
        currentEvent and currentTimex to None."""

        self.xmldoc = xmldoc
        self.doc = Document(filename)


    def convert(self):

        """Loops through the XmlDocument and builds a tree."""
        
        self.current = self.doc

        for el in self.xmldoc.elements:

            if el.is_opening_tag():
                # create the tag and add it to the current node, then
                # set the tag as the new current node
                const = self.tag_as_constituent(el)
                self.current.add_child(const)
                self.current = const
                
            elif el.is_closing_tag():
                # close the current node and replace it with its parent
                self.current = self.current.parent

            elif el.is_text_element():
                # here we do nothing: if a text element is inside a
                # lex then it was already added to the token, if it is
                # not inside a lex then we are not even interested
                pass

        return self.doc
    
            
    def tag_as_constituent(self, opening_element):

        """This method determines what kind of object is added to the
        tree. All objects need to have a parent instance variable. And
        all objects, with the possible exception of Token, need to
        have an add_child method."""
        
        if opening_element.tag == SENTENCE:
            return Sentence()

        elif opening_element.tag == NOUNCHUNK:
            return NounChunk

        elif opening_element.tag == VERBCHUNK:
            return VerbChunk
        
        elif opening_element.tag == TOKEN:
            pos = opening_element.attrs[POS]
            lemma = opening_element.attrs['lemma']
            lid = opening_element.attrs[LID]    
            string = opening_element.next.content
            if pos.startswith(POS_ADJ):
                token = AdjectiveToken(self.doc, opening_element, string)
            else:
                token = Token(self.doc, opening_element, string)
            return token

        elif opening_element.tag == EVENT:
            event = EventTag(opening_element.attrs)
            # need to add instance info
            return event

        elif opening_element.tag == TIMEX:
            return TimexTag(opening_element.attrs)

        else:
            logger.warn('Unexpected element: ' + str(opening_element))



class FragmentConverter:

    """Takes a fragment formatted as a simple list of xml elements (an
    XmlDocument object) and converts it into a shallow tree implemented
    as a Document object. Also maintains lists and dictionaries of
    events, instances, and links.

    Instance variables:
       xmldoc - an XmlDocument
       doc - a Document
       currentSentence - None or a Sentence 
       currentChunk - None or a NounChunk or VerbChunk
       currentToken - None or a Token or AdjectiveToken
       currentTimex - None or a TimexTag
       currentEvent - None or an EventTag
       tree_tags - a list of tags that can be internal nodes
       tag_stack - a stack that keeps track of tag embedding

    The Document instance in doc contains a list of Sentences where
    each Sentence is a list of Tokens and Chunks (and in some cases
    Timexes). Chunks can contain TimexTags and EventTags. EventTags
    are embedded in Chunks or Sentences (the latter for adjectival
    events) and Tokens are embedded in Events, TimexTags, Chunks or
    Sentences.

    Sentence tags, chunk tags, event tags and timex tags are the only
    tags that can form internal constituents. Lex tags are always
    leaves. All other tags are ignored for the tree, but link tags and
    instance tags are used to add data outside the tree.

    Here is an example pretty print of a short Sentence:
    
      <NG>
        <lex pos="PP" text="He">
      <VG>
         <EVENT eid=e6 eiid=ei6 class=OCCURRENCE>
            <lex pos="VBD" text="slept">
      <lex pos="IN" text="on">
      <NG>
         <TIMEX3 tid=t2 TYPE=DATE VAL=20070525TNI>
            <lex pos="NNP" text="Friday">
            <lex pos="NN" text="night">
      <lex pos="." text="."> """


    def __init__(self, xmldoc, filename=None):
        """Initializes xmldoc and doc, using two arguments: xmldoc (an
        XmlDocument) and filename (a string). Also sets instance
        variables currentSentence, currentChunk, currentToken,
        currentEvent and currentTimex to None."""
        self.xmldoc = xmldoc
        self.doc = Document(filename)
        self.currentSentence = None
        self.currentChunk = None
        self.currentToken = None
        self.currentTimex = None
        self.currentEvent = None
        # tags that participate in building the tree
        self.tree_tags = [SENTENCE, NOUNCHUNK, VERBCHUNK, EVENT, TIMEX]
        self.tag_stack = []

        
    def convert(self):
        """Convert the flat list of XML elements in xmldoc into a Document and
        store it in self.doc. Returns the value of self.doc."""
        for element in self.xmldoc:
            if element.is_opening_tag():
                self._process_opening_tag(element)
            elif element.is_closing_tag():         
                self._process_closing_tag(element)
            else:
                self._process_element(element)
            self.doc.addDocNode(element.content)
        return self.doc

    def _process_opening_tag(self, element):
        """Process an opening tag, calling the appropriate handler depending
        on the tag."""
        #logger.debug("ELEMENT: %s ,  %s" % (element.content, self._tag_stack_as_string()))
        if element.tag == SENTENCE:
            self._process_opening_sentence(element)
        elif element.tag == NOUNCHUNK:
            self._process_opening_chunk(NounChunk, element)
        elif element.tag == VERBCHUNK:
            self._process_opening_chunk(VerbChunk, element)
        elif element.tag == TOKEN:
            self._process_opening_lex(element)
        elif element.tag == EVENT:
            self._process_opening_event(element)
        elif element.tag == INSTANCE:
            self._process_opening_make_instance(element)
        elif element.tag == TIMEX:
            self._process_opening_timex(element)
        elif element.tag == ALINK:
            self._process_alink(element)
        elif element.tag == SLINK:
            self._process_slink(element)
        elif element.tag == TLINK:
            self._process_tlink(element)
        if element.tag in self.tree_tags:
            self.tag_stack.append(element.tag)
        
    def _process_opening_sentence(self, element):
        """Create a Sentence and add it to the document."""
        self.currentSentence = Sentence()
        self.doc.addSentence(self.currentSentence)
        
    def _process_opening_chunk(self, chunk_class, element):
        """Create a VerbChunk or NounChunk and add it to the current sentence
        or the current timex."""
        self.currentChunk = chunk_class(element.tag)
        if self._current_node_is_sentence():
            self.currentSentence.add(self.currentChunk)
        elif self._current_node_is_timex():
            self.currentTimex.add(self.currentChunk)
        else:
            logger.warn("No place to put chunk " + `element`)
            
    def _process_opening_lex(self, element):
        """Creates a Token or AdjectviveToken and adds it to the current timex,
        current chunk, or to the current sentence."""
        pos = element.attrs[POS]
        #lid = element.attrs[LID]
        lid = element.attrs.get(LID, 'l0')
        if pos.startswith(POS_ADJ):
            self.currentToken = AdjectiveToken(self.doc, pos, lid)
            if self.currentEvent is not None:
                self.currentToken.setEventInfo(self.currentEvent.attrs[EID])
        else:
            self.currentToken = Token(self.doc, pos, lid)
        # this is needed for later when tokens and events are swapped,
        # the default is that a token does not contain an event, this
        # can be changed when an event tag is processed
        self.currentToken.contains_event = False
        self.currentToken.lex_tag_list.append(element)
        # previously, just checked the truth of self.currentChunk and
        # self.currentSentence, which worked fine for the latter but
        # not for the former (no idea why that was the case, MV)
        if self._current_node_is_timex():
            #logger.debug('    adding token to timex')
            self.currentTimex.add(self.currentToken)
        elif self._current_node_is_chunk():
            #logger.debug('    adding token to chunk')
            self.currentChunk.addToken(self.currentToken)
        elif self._current_node_is_sentence():
            #logger.debug('    adding token to sentence')
            self.currentSentence.add(self.currentToken)
        elif self._current_node() == 'EVENT':
            if self.currentChunk is not None: self.currentChunk.addToken(self.currentToken)
            else: self.currentSentence.add(self.currentToken)
        else:
            logger.warn("No place to put token" + `element`)

    def _process_opening_event(self, element):
        """Creates an EventTag and add it to the event dictionary on the
        Document instance. Also sets the contains_event flag on the
        current token to indicate that the token has an event embedded
        in it (due to an Evita peculiarity of embedding events inside
        of tokens). The EventTag is not added to any constituent,
        _massage_doc takes care of that."""
        event = EventTag(element.attrs)
        self.currentEvent = event
        eid = event.attrs[EID]
        self.doc.event_dict[eid] = event
        if self.currentToken:
            self.currentToken.contains_event = True
            # add event info to containing adjective tokens and chunks, it
            # is not set on other tokens because they do not respond to
            # setEventInfo
            if self.currentToken.isAdjToken():
                self.currentToken.setEventInfo(eid)
            self.currentToken.event_tag = event
        elif self._current_node_is_chunk():
            self.currentChunk.setEventInfo(eid)
            self.currentChunk.dtrs.append(event)
            
    def _process_opening_make_instance(self, element):
        """Creates an InstanceTag and adds it to the instance dictionary on
        the Document. Also copies all attributes on the instance to
        the event. The InstanceTag is not added to a Chunk or Sentence
        or any other element of the shallow tree."""
        instance = InstanceTag(element.attrs)
        eid = instance.attrs[EVENTID]
        eiid = instance.attrs[EIID]
        for (key, value) in instance.attrs.items():
            if key == EVENTID: continue
            self.doc.event_dict[eid].attrs[key] = value
        self.doc.instance_dict[eiid] = instance

    def _process_opening_timex(self, element):
        """Creates a TimeTag and embed it in the current chunk if there is
        one, otherwise add it to the sentence."""
        self.currentTimex = TimexTag(element.attrs)
        logger.debug(str(self.currentTimex.__dict__))
        logger.debug('TYPE:'+ str(type(self.currentTimex)))
        if self._current_node_is_chunk():
            self.currentChunk.addToken(self.currentTimex)
        elif self._current_node_is_sentence():
            self.currentSentence.add(self.currentTimex)
        else:
            logger.warn("No place to put timex " + `element`)
            
    def _process_alink(self, element):
        """Add an AlinkTag to the Alinks list on the Document."""
        alink = AlinkTag(element.attrs)
        self.doc.alink_list.append(alink)
    
    def _process_slink(self, element):
        """Add an SlinkTag to the Slinks list on the Document."""
        slink = SlinkTag(element.attrs)
        self.doc.slink_list.append(slink)
        
    def _process_tlink(self, element):
        """Add an TlinkTag to the Tlinks list on the Document."""
        tlink = TlinkTag(element.attrs)
        self.doc.tlink_list.append(tlink)
    
    def _process_closing_tag(self, element):
        """Resets currentSentence or other currently open constituent to None,
        depending on the closing tag.""" 
        #logger.debug("ELEMENT: %s ,  %s" %
        #             (element.content, self._tag_stack_as_string()))
        if element.tag == SENTENCE: self.currentSentence = None
        if element.tag == NOUNCHUNK: self.currentChunk = None
        if element.tag == VERBCHUNK: self.currentChunk = None
        if element.tag == TOKEN:
            self.currentToken.lex_tag_list.append(element)
            #currentEvent has empty dtrs, and so evaluates to false
            #in boolean context (because __len__ returns 0)
            if self.currentEvent is not None:
                self.currentEvent.dtrs = [self.currentToken]
                if self.currentToken.isAdjToken():
                    self.currentToken.setEventInfo(self.currentEvent.attrs[EID])
            self.currentToken = None
        if element.tag == EVENT: self.currentEvent = None
        if element.tag == TIMEX: self.currentTimex = None
        if element.tag in self.tree_tags:
            self.tag_stack.pop()

    def _process_element(self, element):
        """Non-tags are treated as text nodes and added to the current token
        if there is one."""
        #logger.debug('ELEMENT: "'+element.content+'"')
        if self.currentToken != None:
            self.currentToken.setTextNode(self.doc.nodeCounter)
            self.currentToken.lex_tag_list.append(element)            
        elif not element.content.isspace():
            # this spots those cases where a non-empty text string is
            # not tokenized should only occur outside of the content
            # tag
            logger.warn("No token to put non-empty cdata element '" +
                        element.content + "'")
            
    def _current_node_is_timex(self):
        """Return True if the current node is a timex and self.currentTimex is
        not None, return False otherwise"""
        return self._current_node() == TIMEX and self.currentTimex is not None

    def _current_node_is_chunk(self):
        """Return True if the current node is a noun chunk or verb chunk and
        self.currentChunk is not None, return False otherwise"""
        return self._current_node() in [NOUNCHUNK, VERBCHUNK] and \
            self.currentChunk is not None

    def _current_node_is_sentence(self):
        """Return True if the current node is a sentence and
        self.currentSentence is not None, return False otherwise"""
        return self._current_node() == SENTENCE and self.currentSentence is not None
        
    def _current_node(self):
        """Return the category of the currently open constituent, return None
        if there is no open constituent. The open consituent is the
        one on top of the stack."""
        try:
            return self.tag_stack[-1]
        except IndexError:
            logger.warning("No open node available")
            return None
        
    def _tag_stack_as_string(self):
        """Return self.tag_stack as a pretty string."""
        return "STACK: [" + ' '.join(self.tag_stack) + ']'

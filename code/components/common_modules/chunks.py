"""Implements the behaviour of chunks.

Chunks are embedded in sentences and contain event tags, timex tags and
instances of Token.

Much of the functionality of Evita and Slinket is delegated to chunks.

"""

import string
from types import ListType, TupleType

import library.forms as forms
import library.patterns as patterns
from library.timeMLspec import FORM, STEM, POS, TENSE, ASPECT, EPOS, MOD, POL
from library.timeMLspec import EVENTID, EIID, CLASS, EVENT, TIMEX
from utilities import logger
from components.common_modules.constituent import Constituent
from components.evita.event import Event
from components.evita.gramChunk import GramNChunk, GramVChunkList


# This is another way of capturing messages. It is separate from the logger and
# operates class based. It is used in VerbChunk to collect data from a run.
DRIBBLE = False


def update_event_checked_marker(constituent_list):
    """Update Position in sentence, by marking as already checked for EVENT the
    Tokens and Chunks in constituent_list. These are constituents that are
    included in a chunk where an event was found."""
    for item in constituent_list:
        item.setCheckedEvents()

def get_tokens(sequence):
    """Given a sequence of elements which is a slice of a tree, collect all
    token leaves and return them as a list."""
    tokens = []
    for item in sequence:
        if item.nodeType[-5:] == 'Token':
            tokens.append(item)
        elif item.nodeType[-5:] == 'Chunk':
            tokens += get_tokens(item)
        elif item.nodeType == 'EVENT':
            tokens.append(item)
        elif item.nodeType == 'TIMEX3':
            tokens += get_tokens(item)
        else:
            raise "ERROR: unknown item type: " + item.nodeType
    return tokens


class Chunk(Constituent):

    """Implements the common behaviour of chunks. Chunks are embedded in sentences and
    contain event tags, timex tags and tokens.

    Instance variables
       phraseType         - string indicating the chunk type, usually 'VG' or 'NG'
       dtrs = []          - a list of Tokens, EventTags and TimexTags
       position = None    - index in the parent's daughters list
       head = -1          - the index of the head of the chunk
       parent = None      - the parent, an instance of Sentence typically
       gramchunk = None   - an instance of GramNChunk or GramVChunk
       gramchunks = []    - a list of GramVChunks, used for verb chunks
       event = None
       eid = None
       checkedEvents = False

    """
    
    def __init__(self, phraseType):
        self.phraseType = phraseType
        self.dtrs = []
        self.position = None
        self.parent = None
        self.begin = None
        self.end = None
        self.head = -1
        self.gramchunk = None
        self.gramchunks = []
        self.event = None
        self.eid = None
        self.checkedEvents = False

    def __len__(self):
        """Returns the lenght of the dtrs variable."""
        return len(self.dtrs)

    def __setitem__(self, index, val):
        """Sets a value on the dtrs variable."""
        self.dtrs[index] = val

    def __getitem__(self, index):
        """Returns an element from the dtrs variable."""
        return self.dtrs[index]

    def __getslice__(self, i, j):
        """Get a slice from the dtrs variable."""
        return self.dtrs[i:j]

    def getHead(self):
        """Return the head of the chunk (by default the last element)."""
        return self.dtrs[self.head]

    def __getattr__(self, name):
        """Used by Sentence._match. Needs cases for all instance variables used in the
        pattern matching phase. This is almost identical to the same method on Token, do
        this a bit more elegantly."""
        # TODO: removing this method did not seem to make a difference. Perhaps
        # it was moved to GramNChunk, which was changed to allow removing
        # __getattr__. When matching functionality shifts back to Chunk, may
        # need to go through that excercise again.
        # NOTE: removing it crashed Slinket
        if name == 'nodeType':
            return self.__class__.__name__
        if name == 'nodeName':
            return self.phraseType
        if name == 'text':
            return None
        if name == 'pos':
            return None
        if name in ['eventStatus', 'text', FORM, STEM, POS, TENSE, ASPECT,
                      EPOS, MOD, POL, EVENTID, EIID, CLASS]:
            if not self.event:
                return None
            doc = self.parent.document()
            if name == 'eventStatus':
                return '1'
            if name == 'text' or name == FORM:
                return doc.taggedEventsDict[self.eid][FORM] 
            if name == MOD:
                return doc.taggedEventsDict[self.eid].get(MOD,'NONE')
            if name == POL:
                return doc.taggedEventsDict[self.eid].get(POL,'POS')
            if name == POS:
                return doc.taggedEventsDict[self.eid].get(POS,'NONE')
            return doc.taggedEventsDict[self.eid][name]
        else:
            raise AttributeError, name
        
    def _processEventInChunk(self, gramChunk=None):
        """Perform a few little checks on the head and check whether there is an
        event class, then add the event to the document. When this is called on
        a NounChunk, then there is no GramChunk handed in and it will be
        retrieved from the gramchunk instance variable, when it is called from
        VerbChunk, then the GramChunk will be handed in."""
        gchunk = self.gramchunk if gramChunk is None else gramChunk
        # TODO: the second and third test seem relevant for verbs only
        if (gchunk.head
            and gchunk.head.getText() not in forms.be
            and gchunk.head.getText() not in forms.spuriousVerb
            and gchunk.evClass):
            self.document().addEvent(Event(gchunk))

    # the next methods (up to, but not including addToken) were all taken from the
    # slinket/s2t version.
    
    def _matchChunk(self, chunkDescription):

        """Match the chunk instance to the patterns in chunkDescription, which
        is a dictionary with keys-values pairs that match instance variables and
        their values on GramChunks.

        The value in key-value pairs can be:
        - an atomic value. E.g., {..., 'headForm':'is', ...} 
        - a list of possible values. E.g., {..., headForm': forms.have, ...}   
        In this case, _matchChunk checks whether the chunk feature is
        included within this list.
        - a negated value. It is done by introducing it as
        a second constituent of a 2-position tuple whose initial position
        is the caret symbol: '^'. E.g., {..., 'headPos': ('^', 'MD') ...}
        
        This method is also implemented on Constituent."""

        # TODO: removing this method had no impact on Evita, find out why, but
        # note that it might impact Slinket

        #logger.debug(str(chunkDescription))
        for feat in chunkDescription.keys():
            value = chunkDescription[feat]
            #print feat, type(value), value
            if type(value) is TupleType:
                if value[0] == '^':
                    newvalue = self._hackToSolveProblemsInValue(value[1])
                    if type(newvalue) is ListType:
                        if self.__getattr__(feat) in newvalue:
                            return 0
                    else:
                        if self.__getattr__(feat) == newvalue:
                            return 0
                else:
                    raise "ERROR specifying description of pattern" 
            elif type(value) is ListType:
                if self.__getattr__(feat) not in value:
                    # this is where this one differs from the one on Constituent
                    #print 'feature text matters!'
                    #print feat, type(value), value
                    if feat != 'text':
                        return 0
                    else:
                        if self._getHeadText() not in value:
                            return 0
            else:
                value = self._hackToSolveProblemsInValue(value)
                if self.__getattr__(feat) != value:
                    return 0
        return 1


    def _getHeadText(self):
        headText = string.split(self.getText())[-1]
        return headText.strip()

    def embedded_event(self):
        """Returns the embedded event of the chunk if it has one, returns None
        otherwise."""
        # TODO: check whether this is needed outside of the arglinker
        # NOTE: yes, it is used to get the events for slinket
        for item in self:
            if item.isEvent():
                return item
        return None

    # end of methods from SLinket/S2T version of this class

    def addToken(self, token):
        token.setParent(self)
        self.dtrs.append(token)

    def setEventInfo(self, eid):
        self.event = 1
        self.eid = eid
        
    def getText(self):
        string = ""
        for token in self.dtrs:
            string += ' ' + str(token.getText())
        return string

    def isChunk(self):
        """Returns True."""
        return True

    def isTimex(self):
        """Return True if the chunk is a Timex chunk."""
        return self.phraseType and self.phraseType[:5] == 'TIMEX'

    def pretty_print(self, indent=0):
        print "%s<%s position=%s checkedEvents=%s event=%s eid=%s>" % \
            (indent * ' ', self.__class__.__name__,
             self.position, self.checkedEvents, self.event, self.eid)
        for tok in self.dtrs:
            tok.pretty_print(indent+2)

        
class NounChunk(Chunk):

    """Behaviour specific to noun chunks, most notably the NounChunk specific
    code to create events."""

    def isNounChunk(self):
        """Returns True"""
        return True

    def isDefinite(self):
        """Return True if self includes a Token that is a POS, PRP$ or a definite determiner."""
        # TODO: these tags should be defined in forms
        for token in self.dtrs[:self.head]:
            if (token.pos == 'POS'
                or token.pos == 'PRP$'
                or (token.pos in ('DT', 'DET')
                   and token.getText() in forms.definiteDeterminers)):
                return True
        return False

    def isEmpty(self):
        """Return True if the chunk is empty, False otherwise."""
        if not self.dtrs:
            # this happened at some point due to a crazy bug in the converter
            # code (as noted on 11/08/07)
            logger.warn("There are no dtrs in the NounChunk")
            return True
        return False

    def createEvent(self, verbGramFeat=None, tarsqidoc=None):
        """Try to create an event in the NounChunk. Checks whether the nominal is an
        event candidate, then conditionally adds it. The verbGramFeat dictionary
        is used when a governing verb hands in its features to a nominal in a
        predicatve complement."""
        logger.debug("NounChunk.createEvent(verbGramFeat=%s)" % verbGramFeat)
        if not self.isEmpty():
            self.gramchunk = GramNChunk(self)
            self.gramchunk.add_verb_features(verbGramFeat)
            logger.debug(self.gramchunk.as_verbose_string())
            # Even if preceded by a BE or a HAVE form, only tagging N Chunks headed by an
            # eventive noun E.g., "was an intern" will NOT be tagged
            if self.gramchunk.isEventCandidate():
                logger.debug("Nominal is an event candidate")
                self._processEventInChunk()


class VerbChunk(Chunk):

    if DRIBBLE:
        DRIBBLE_FH = open("dribble-VerbChunk.txt", 'w')

    def dribble(self, header, text):
        """Write information on the sentence that an event was added to."""
        if DRIBBLE:
            toks = get_tokens(self.parent.dtrs)
            p1 = int(toks[0].lex.attrs['begin'])
            p2 = int(toks[-1].lex.attrs['end'])
            e_p1 = self.dtrs[-1].lex.attrs['begin']
            e_p2 = self.dtrs[-1].lex.attrs['end']
            text = ' '.join(text.split())
            sentence = self.tarsqidoc.source.text[p1:p2]
            sentence = ' '.join(sentence.split())
            line = "%s\t%s\t%s\t%s:%s\n" % (header, text, sentence, e_p1, e_p2)
            VerbChunk.DRIBBLE_FH.write(line)

    def isVerbChunk(self):
        """Return True."""
        return True

    # The following methods are all from what was orginally a stand-alone Evita
    # version of this class.

    def _identify_substring(self, sentence_slice, fsa_list):
        """Similar to Constituent._identify_substring(), except that this method
        calls acceptsSubstringOf() instead of acceptsShortestSubstringOf()."""
        # TODO: Slinket threw an error when this method was included. Find out
        # if that is still the case and why this one was needed, that is, why
        # not use the shortest substring.
        # NOTE: Using this results in two extra events on the evita-test2.sh
        # regression test. Also, it does not crash SLinket anymore.
        fsaCounter = -1
        for fsa in fsa_list:
            fsaCounter += 1
            lenSubstring = fsa.acceptsSubstringOf(sentence_slice)
            if lenSubstring:
                return (lenSubstring, fsaCounter)
        else:
            return (0, fsaCounter)

    def _getRestSent(self, structure):
        """Obtaining the rest of the sentence, which can be in a flat,
        token-based structure, or chunked."""
        logger.debug("Entering _getRestSent")
        if structure == 'flat':
            restSentence = get_tokens(self.parent[self.position+1:])
        elif structure == 'chunked':
            restSentence = self.parent[self.position+1:]
        else:
            raise "ERROR: unknown structure value"
        return restSentence
            
    def _lookForMultiChunk(self, FSA_set, STRUCT='flat'):
        """Default argument 'STRUCT' specifies the structural format of the rest of the
        sentence: either a flat, token-level representation or a chunked one."""
        logger.debug("Entering _lookForMultiChunk")
        restSentence = self._getRestSent(STRUCT)
        if STRUCT == 'flat':
            for item in restSentence:
                logger.debug("\t "+item.getText()+" "+item.pos)
        lenSubstring, fsaNum = self._identify_substring(restSentence, FSA_set)
        if lenSubstring:
            logger.debug("ACCEPTED by FSA, LENGTH:"+ str(lenSubstring) + "FSA:" + str(fsaNum))
            return restSentence[:lenSubstring]
        else:
            logger.debug("REJECTED by FSA:" + str(fsaNum))
            return 0

    def _processEventInMultiVChunk(self, substring):
        chunk_list = get_tokens(self) + substring
        GramMultiVChunk = GramVChunkList(chunk_list)[0]
        self._processEventInChunk(GramMultiVChunk)
        map(update_event_checked_marker, substring)

    def _processEventInMultiNChunk(self, GramVCh, substring):
        nounChunk = substring[-1]
        verbGramFeatures = {'tense': GramVCh.tense,
                            'aspect': GramVCh.aspect,
                            'modality': GramVCh.modality,
                            'polarity': GramVCh.polarity}
        nounChunk.createEvent(verbGramFeatures)
        map(update_event_checked_marker, substring)

    def _processEventInMultiAChunk(self, GramVCh, substring):
        adjToken = substring[-1]
        verbGramFeatures = {'tense': GramVCh.tense,
                            'aspect': GramVCh.aspect,
                            'modality': GramVCh.modality,
                            'polarity': GramVCh.polarity}
        adjToken.createAdjEvent(verbGramFeatures)
        map(update_event_checked_marker, substring)

    def _processDoubleEventInMultiAChunk(self, GramVCh, substring):
        """Tagging EVENT in VerbChunk and in AdjectiveToken."""
        logger.debug("[V_2Ev] " + GramVCh.as_verbose_string())
        self._processEventInChunk(GramVCh)
        adjToken = substring[-1]
        adjToken.createAdjEvent()
        map(update_event_checked_marker, substring)

        
    def _createEventOnRightmostVerb(self, GramVCh):

        if GramVCh.nodeIsNotEventCandidate():
            return

        self_text = self.getText()
        next_node = self.nextNode()

        if GramVCh.nodeIsModalForm(next_node):
            logger.debug("Checking for modal pattern...")
            substring = self._lookForMultiChunk(patterns.MODAL_FSAs)
            if substring:
                self.dribble("MODAL", self_text)
                self._processEventInMultiVChunk(substring)

        elif GramVCh.nodeIsBeForm(next_node):
            logger.debug("Checking for BE + NOM Predicative Complement...")
            substring = self._lookForMultiChunk(patterns.BE_N_FSAs, 'chunked')
            if substring:
                self.dribble("BE-NOM", self_text)
                self._processEventInMultiNChunk(GramVCh, substring)
            else:
                logger.debug("Checking for BE + ADJ Predicative Complement...")
                substring = self._lookForMultiChunk(patterns.BE_A_FSAs, 'chunked')
                if substring:
                    matched = self_text + ' ' + ' '.join([s.getText() for s in substring])
                    self.dribble("BE-ADJ", matched)
                    self._processEventInMultiAChunk(GramVCh, substring)  
                else:
                    logger.debug("Checking for BE + VERB Predicative Complement...")
                    substring = self._lookForMultiChunk(patterns.BE_FSAs)
                    if substring:
                        self.dribble("BE-V", self_text)
                        self._processEventInMultiVChunk(substring)

        elif GramVCh.nodeIsHaveForm():
            logger.debug("Checking for toHave pattern...")
            substring = self._lookForMultiChunk(patterns.HAVE_FSAs)
            if substring:
                self.dribble("HAVE-1", self_text)
                self._processEventInMultiVChunk(substring)
            else:
                self.dribble("HAVE-2", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsFutureGoingTo():
            logger.debug("Checking for futureGoingTo pattern...")
            substring = self._lookForMultiChunk(patterns.GOINGto_FSAs)
            if substring:
                self.dribble("GOING-TO", self_text)
                self._processEventInMultiVChunk(substring)
            else:
                self.dribble("GOING", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsPastUsedTo():
            logger.debug("Checking for pastUsedTo pattern...")
            substring = self._lookForMultiChunk(patterns.USEDto_FSAs)
            if substring:
                self.dribble("USED-1", self_text)
                self._processEventInMultiVChunk(substring)
            else:
                self.dribble("USED-2", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsDoAuxiliar():
            logger.debug("Checking for doAuxiliar pattern...")
            substring = self._lookForMultiChunk(patterns.DO_FSAs)
            if substring:
                self.dribble("DO-AUX", self_text)
                self._processEventInMultiVChunk(substring)
            else:
                self.dribble("DO", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsBecomeForm(next_node):
            # Looking for BECOME + ADJ Predicative Complement e.g., He became famous at
            # the age of 21
            logger.debug("Checking for BECOME + ADJ Predicative Complement...")
            substring = self._lookForMultiChunk(patterns.BECOME_A_FSAs, 'chunked')
            if substring:
                self.dribble("BECOME-ADJ", self_text)
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self.dribble("BECOME", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsContinueForm(next_node):
            # Looking for CONTINUE + ADJ Predicative Complement e.g., Interest rate
            # continued low.
            logger.debug("Checking for CONTINUE + ADJ...")
            substring = self._lookForMultiChunk(patterns.CONTINUE_A_FSAs, 'chunked')
            if substring:
                self.dribble("CONTINUE-ADJ", self_text)
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self.dribble("CONTINUE", self_text)
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsKeepForm(next_node):
            # Looking for KEEP + ADJ Predicative Complement e.g., The announcement kept
            # everybody Adj.
            logger.debug("Checking for KEEP + [NChunk] + ADJ...")
            substring = self._lookForMultiChunk(patterns.KEEP_A_FSAs, 'chunked')
            if substring:
                self.dribble("KEEP-N-ADJ", self_text)
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self.dribble("KEEP", self_text)
                self._processEventInChunk(GramVCh)

        else:
            self.dribble("OTHER", self_text)
            logger.debug("General case")
            self._processEventInChunk(GramVCh)


    def createEvent(self, tarsqidoc):
        """Try to create an event in the VerbChunk. Delegates to two methods
        depending on the position of the verb in the chunk."""

        self.tarsqidoc = tarsqidoc
        GramVChList = GramVChunkList(self)
        if GramVChList.do_not_process():
            return
        logger.debug("len(GramVChList) = %d" % len(GramVChList))
        for gramchunk in GramVChList:
            logger.debug(gramchunk.as_verbose_string())
        if len(GramVChList) == 1:
            self._createEventOnRightmostVerb(GramVChList[-1])
        else:
            self.dribble('COMPLEX', '')
            lastIdx = len(GramVChList) - 1
            for idx in range(len(GramVChList)):
                gramVCh = GramVChList[idx]
                if idx == lastIdx:
                    self._createEventOnRightmostVerb(gramVCh)
                else:
                    logger.debug("[Not Last] " + gramVCh.as_verbose_string())
                    if not gramVCh.isAuxVerb():
                        self._processEventInChunk(gramVCh)

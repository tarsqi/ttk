"""Implements the behaviour of chunks.

Chunks are embedded in sentences and contain event tags, timex tags and
instances of Token.

Much of the functionality of Evita and Slinket is delegated to chunks.

"""

import library.forms as forms
import library.patterns as patterns
from library.timeMLspec import FORM, STEM, POS, TENSE, ASPECT, EPOS, MOD, POL
from library.timeMLspec import EVENTID, EIID, CLASS, EVENT, TIMEX

from components.common_modules import utils
from components.common_modules.constituent import Constituent

from components.evita.event import Event
from components.evita.gramChunk import GramNChunk, GramVChunkList
from components.evita import wordnet
from components.evita import bayes

from components.evita.settings import EVITA_NOM_DISAMB
from components.evita.settings import EVITA_NOM_CONTEXT
from components.evita.settings import EVITA_NOM_WNPRIMSENSE_ONLY

from utilities import logger


# Get the Bayesian event recognizer
nomEventRec = bayes.get_classifier()


# This is another way of capturing messages. It is separate from the logger and
# operates class based. It is used in VerbChunk to collect data from a run.
DRIBBLE = False


def update_event_checked_marker(constituent_list):
    """Update Position in sentence, by marking as already checked for EVENT the
    Tokens and Chunks in constituent_list. These are constituents that are
    included in a chunk where an event was found."""
    for item in constituent_list:
        item.setCheckedEvents()


class Chunk(Constituent):

    """Implements the common behaviour of chunks. Chunks are embedded in sentences and
    contain event tags, timex tags and tokens.

    Instance variables
       phraseType         - string indicating the chunk type, either 'vg' or 'ng'
       parent = None      - the parent of the chunk
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
        Constituent.__init__(self)
        self.phraseType = phraseType
        self.position = None
        self.head = -1
        self.gramchunk = None
        self.gramchunks = []
        self.event = None
        self.eid = None
        self.checkedEvents = False

    def __getattr__(self, name):
        """Used by Sentence._match. Needs cases for all instance variables used in the
        pattern matching phase. A similar method is used on Token. Used by Slinket"""
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
            if name == 'eventStatus':
                return '1'
            if name == 'text' or name == FORM:
                return self.tree.events[self.eid][FORM]
            if name == MOD:
                return self.tree.events[self.eid].get(MOD,'NONE')
            if name == POL:
                return self.tree.events[self.eid].get(POL,'POS')
            if name == POS:
                return self.tree.events[self.eid].get(POS,'NONE')
            return self.tree.events[self.eid][name]
        else:
            raise AttributeError, name

    def getHead(self):
        """Return the head of the chunk (by default the last element)."""
        return self.dtrs[self.head]

    def _processEventInChunk(self, gramChunk=None):
        """Perform a few little checks on the head and check whether there is an
        event class, then add the event to the tree. When this is called on
        a NounChunk, then there is no GramChunk handed in and it will be
        retrieved from the gramchunk instance variable, when it is called from
        VerbChunk, then the GramChunk will be handed in."""
        gchunk = self.gramchunk if gramChunk is None else gramChunk
        # TODO: the second and third test seem relevant for verbs only
        if (gchunk.head
            and gchunk.head.getText() not in forms.be
            and gchunk.head.getText() not in forms.spuriousVerb
            and gchunk.evClass):
            self.tree.addEvent(Event(gchunk))

    def _getHeadText(self):
        """Get the text string of the head of the chunk. Used by matchConstituent."""
        headText = self.getText().split()[-1]
        return headText.strip()

    def embedded_event(self):
        """Returns the embedded event of the chunk if it has one, returns None
        otherwise. It is used to get the events for slinket"""
        for item in self:
            if item.isEvent():
                return item
        return None

    def isChunk(self):
        """Returns True."""
        return True

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
        """Return True if self includes a Token that is a POS, PRP$ or a definite
        determiner."""
        for token in self.dtrs[:self.head]:
            if (token.pos == forms.possessiveEndingTag
                or token.pos == forms.possessivePronounTag
                or (token.pos in forms.determinerTags
                   and token.getText() in forms.definiteDeterminers)):
                return True
        return False

    def isEmpty(self):
        """Return True if the chunk is empty, False otherwise."""
        return False if self.dtrs else True

    def createEvent(self, gramvchunk=None):
        """Try to create an event in the NounChunk. Checks whether the nominal is an
        event candidate, then conditionally adds it. The gramvchunk dictionary
        is used when a governing verb hands in its features to a nominal in a
        predicative complement."""
        logger.debug("NounChunk.createEvent(gramvchunk=%s)")
        if self.isEmpty():
            # this happened at some point due to a crazy bug in some old code
            # that does not exist anymore, let's log a warning in case this
            # problem returns
            logger.warn("There are no dtrs in the NounChunk")
        else:
            self.gramchunk = GramNChunk(self, gramvchunk)
            logger.debug(self.gramchunk.as_verbose_string())
            # Even if preceded by a BE or a HAVE form, only tagging N Chunks
            # headed by an eventive noun E.g., "was an intern" will NOT be
            # tagged
            #if self.gramchunk.isEventCandidate():
            if self.isEventCandidate():
                logger.debug("Nominal is an event candidate")
                self._processEventInChunk()

    def isEventCandidate(self):
        """Return True if the nominal is syntactically and semantically an
        event, return False otherwise."""
        return self.isEventCandidate_Syn() and self.isEventCandidate_Sem()

    def isEventCandidate_Syn(self):
        """Return True if the GramNChunk is syntactically able to be an event,
        return False otherwise. An event candidate syntactically has to have a
        head (which cannot be a timex) and the head has to be a common noun."""
        # using the regular expression is a bit faster then lookup in the short
        # list of common noun parts of speech (forms.nounsCommon)
        return (
            self.gramchunk.head
            and not self.gramchunk.head.isTimex()
            and forms.RE_nounsCommon.match(self.gramchunk.head.pos) )

    def isEventCandidate_Sem(self):
        """Return True if the GramNChunk can be an event semantically. Depending
        on user settings this is done by a mixture of wordnet lookup and using a
        simple classifier."""
        logger.debug("event candidate?")
        lemma = self.gramchunk.getEventLemma()
        # return True if all WordNet senses are events, no classifier needed
        is_event = wordnet.allSensesAreEvents(lemma)
        logger.debug("  all WordNet senses are events ==> %s" % is_event)
        if is_event:
            return True
        # run the classifier if required, fall through on disambiguation error
        if EVITA_NOM_DISAMB:
            try:
                is_event = self._run_classifier(lemma)
                logger.debug("  baysian classifier result ==> %s" % is_event)
                return is_event
            except bayes.DisambiguationError, (strerror):
                pass
                logger.debug("  DisambiguationError: %s" % unicode(strerror))
        # check whether primary sense or some of the senses are events
        if EVITA_NOM_WNPRIMSENSE_ONLY:
            is_event = wordnet.primarySenseIsEvent(lemma)
            logger.debug("  primary WordNet sense is event ==> %s" % is_event)
        else:
            is_event = wordnet.someSensesAreEvents(lemma)
            logger.debug("  some WordNet sense is event ==> %s" % is_event)
        return is_event

    def _run_classifier(self, lemma):
        """Run the classifier on lemma, using features from the GramNChunk."""
        features = []
        if EVITA_NOM_CONTEXT:
            features = ['DEF' if self.isDefinite() else 'INDEF',
                        self.gramchunk.head.pos]
        is_event = nomEventRec.isEvent(lemma, features)
        logger.debug("  nomEventRec.isEvent(%s) ==> %s" % (lemma, is_event))
        return is_event



class VerbChunk(Chunk):

    if DRIBBLE:
        DRIBBLE_FH = open("dribble-VerbChunk.txt", 'w')

    def dribble(self, header, text):
        """Write information on the sentence that an event was added to."""
        if DRIBBLE:
            toks = utils.get_tokens(self.parent.dtrs)
            p1 = toks[0].begin
            p2 = toks[-1].end
            e_p1 = self.dtrs[-1].begin
            e_p2 = self.dtrs[-1].end
            text = ' '.join(text.split())
            sentence = self.tree.tarsqidoc.source.text[p1:p2]
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
        calls acceptsSubstringOf() instead of acceptsShortestSubstringOf(). In
        some tests, for example evita-test2.sh, this version results in extra
        events."""
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
            restSentence = utils.get_tokens(self.parent[self.position+1:])
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
        chunk_list = utils.get_tokens(self) + substring
        GramMultiVChunk = GramVChunkList(chunk_list)[0]
        self._processEventInChunk(GramMultiVChunk)
        map(update_event_checked_marker, substring)

    def _processEventInMultiNChunk(self, GramVCh, substring):
        nounChunk = substring[-1]
        nounChunk.createEvent(GramVCh)
        map(update_event_checked_marker, substring)

    def _processEventInMultiAChunk(self, GramVCh, substring):
        adjToken = substring[-1]
        adjToken.createAdjEvent(GramVCh)
        map(update_event_checked_marker, substring)

    def _processDoubleEventInMultiAChunk(self, GramVCh, substring):
        """Tagging EVENT in both VerbChunk and AdjectiveToken. In this case the adjective
        will not be given the verb features."""
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


    def createEvent(self):
        """Try to create an event in the VerbChunk. Delegates to two methods
        depending on the position of the verb in the chunk."""

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

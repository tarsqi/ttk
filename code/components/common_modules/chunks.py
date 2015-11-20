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
from components.evita.gramChunk import GramNChunk, GramAChunk, GramVChunkList  


class Chunk(Constituent):

    """Implements the common behaviour of chunks. Chunks are embedded in sentences and
    contain event tags, timex tags and tokens.

    Instance variables
       phraseType         - string indicating the chunk type, usually 'VG' or 'NG'
       dtrs = []          - a list of Tokens, EventTags and TimexTags
       positionCount = 0
       position = None
       parent = None
       gramchunk = None   - an instance of GramAChunk, GramNChunk or GramVChunk
       gramchunks = []    - used for verb chunks
       event = None
       eid = None
       isEmbedded = 0
       flagCheckedForEvents = 0

    """
    
    def __init__(self, phraseType):
        self.phraseType = phraseType
        self.dtrs = []
        self.positionCount = 0
        self.position = None
        self.parent = None
        self.gramchunk = None
        self.gramchunks = []
        self.event = None
        self.eid = None
        self.isEmbedded = 0
        self.flagCheckedForEvents = 0

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


    def __getattr__(self, name):

        """Used by Sentence._match. Needs cases for all instance variables used in the
        pattern matching phase. This is almost identical to the same method on Token, do
        this a bit more elegantly."""

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

        
    def _createMultiChunk(self, multiChunkEnd): # *** MUST GO to Chunk??
        """for evita."""
        multiChunkInit = self.getTokens(self)
        return multiChunkInit + multiChunkEnd

    def _processEventInChunk(self, gramChunk=None):
        """Perform a few little checks on the head and check whether there is an event
        class, then add the event to the document. When this is called on a
        NounChunk, then there is no GramChunk handed in and it will be retrieved
        from the gramchunk instance variable, when it is called from
        VerbChunk, then the GramChunk will be handed in. """
        doc = self.document()
        gchunk = self.gramchunk if gramChunk is None else gramChunk
        # TODO: the second and third test seem relevant for verbs only
        if (gchunk.head
            and gchunk.head.getText() not in forms.be
            and gchunk.head.getText() not in forms.spuriousVerb
            and gchunk.evClass):
            doc.addEvent(Event(gchunk))

    # the next methods (up to, but not including endVerbs) were all taken from the
    # slinket/s2t version.
    
    def _matchChunk(self, chunkDescription):

        """Match the chunk instance to the patterns in chunkDescriptions.
        chunkDescription is a dictionary with keys-values pairs that match instance
        variables and their values on GramChunks.

        The value in key-value pairs can be:
        - an atomic value. E.g., {..., 'headForm':'is', ...} 
        - a list of possible values. E.g., {..., headForm': forms.have, ...}   
        In this case, _matchChunk checks whether the chunk feature is
        included within this list.
        - a negated value. It is done by introducing it as
        a second constituent of a 2-position tuple whose initial position
        is the caret symbol: '^'. E.g., {..., 'headPos': ('^', 'MD') ...}
        
        This method is also implemented in the chunkAnalyzer.GramChunk class
        """

        for feat in chunkDescription.keys():
            value = chunkDescription[feat]
            #logger.debug("\nVALUE TO MATCH: "+str(feat)+
            #             "\t|| VALUE in expression: "+
            #             str(self.__getattr__(feat)))
            #logger.out('feature', feat, '=', value)
            if type(value) is TupleType:
                #logger.out('value is a Tuple')
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
                #logger.out('value is a List')
                if self.__getattr__(feat) not in value:
                    if feat != 'text':
                        return 0
                    else:
                        #self._getHeadText()
                        if self._getHeadText() not in value:
                            return 0
            else:
                #logger.out('value is something else')
                value = self._hackToSolveProblemsInValue(value)
                #logger.out('value is now', value)
                feat_on_self = self.__getattr__(feat)
                #logger.out('feature on self =', feat_on_self)
                #logger.out('self.event =', self.event)
                if self.__getattr__(feat) != value:
                    #logger.out('match failed')
                    return 0
        return 1


    def _getHeadText(self):
        headText = string.split(self.getText())[-1]
        return headText.strip()

    def embedded_event(self):
        """Returns the embedded event of the chunk if it has one, returns None
        otherwise."""
        for item in self:
            if item.isEvent():
                return item
        return None
            
    def setEmbedded(self):
        """Keeping track of chunks embedded within other chunks, for parsing purposes"""
        self.isEmbedded = 1

    def resetEmbedded(self):
        self.isEmbedded = 0
        
    def startHead(self):
        pass

    def startVerbs(self):
        pass

    def endVerbs(self):
        pass
    
    def addToken(self, token):
        token.setParent(self)
        self.dtrs.append(token)
        self.positionCount += 1

    def setEventInfo(self, eid):
        self.event = 1
        self.eid = eid
        
    def getText(self):
        string = ""
        for token in self.dtrs:
            string = string+' '+token.getText()
            #string = string+' '+str(token.getText())
        return string

    def getTokens(self, sequence):
        """Given a sequence of sentence elements, de-chunk it and return a list of plain
        tokens. Used for mapping sentences slices into RegEx-based patterns."""
        tokensList = []
        for item in sequence:
            if item.nodeType[-5:] == 'Token':
                tokensList.append(item)
            elif item.nodeType[-5:] == 'Chunk':
                chunkTokens = self.getTokens(item)
                tokensList = tokensList + chunkTokens
            elif item.nodeType == 'EVENT':
                tokensList.append(item)
            elif item.nodeType == 'TIMEX3':
                timexTokens = self.getTokens(item)
                tokensList = tokensList + timexTokens
            else:
                raise "ERROR: unknown item type: "+item.nodeType
        return tokensList

    def startHead(self):
        pass

    def isChunk(self):
        return 1

    def isTimex(self):
        if self.phraseType and self.phraseType[:5] == 'TIMEX':
            return 1
        else: return 0

    def isNChHead(self):
        if self.phraseType and self.phraseType[:4] == 'HEAD':
            return 1
        else: return 0

    def pretty_print(self, indent=0):
        print "%s<%s positionCount=%s position=%s isEmbedded=%s, checked=%s eid=%s>" % \
            (indent * ' ', self.__class__.__name__,
             self.positionCount, self.position, self.isEmbedded, self.flagCheckedForEvents, self.eid)
        for tok in self.dtrs:
            tok.pretty_print(indent+2)

        
class AdjChunk(Chunk):

    def __init__(self, phraseType):
        Chunk.__init__(self, phraseType)
        self.head = -1

    def getHead(self):
        return self.dtrs[self.head]

    def isAdjChunk(self):
        return 1
    

class NounChunk(Chunk):

    def __init__(self, phraseType):
        Chunk.__init__(self, phraseType)
        self.head = -1
        self.poss = None

    def getHead(self):
        return self.dtrs[self.head]

    def getPoss(self):
        return self.dtrs[self.poss]

    def startHead(self):
        self.head = len(self.dtrs)

    def startPOSS(self):
        if self.dtrs:
            self.poss = len(self.dtrs)
        else:
            self.poss = 0

    def isNounChunk(self):
        """Returns True"""
        return True

    def isDefinite(self):
        """Return True if self includes a Token that is a POS, PRP$ or a definite determiner."""
        for token in self.dtrs[:self.head]:
            if token.pos == 'POS' or token.pos == 'PRP$':
                return True
            if token.pos in ('DT', 'DET') \
                    and token.getText() in ['the', 'this', 'that', 'these', 'those']:
                return True
        # in the slinket/s2t version, the following line used to be included as
        # an else in the loop above, which seems wrong
        return False

    def isEmpty(self):
        """Return True if the chunk is empty, False otherwise."""
        if not self.dtrs:
            # this happened at some point due to a crazy bug in the converter
            # code (as noted by mv on 11/08/07)
            logger.warn("There are no dtrs in the NounChunk")
            return True
        return False

    def createEvent(self, verbGramFeat=None):
        """Try to create an event in the NounChunk. Checks whether the nominal is an
        event candidate, then conditionally adds it. The verbGramFeat dictionary
        is used when a governing verb hands in its features to a nominal in a
        predicatve complement."""
        logger.debug("NounChunk.createEvent(verbGramFeat=%s)" % verbGramFeat)
        if not self.isEmpty():
            # TODO: find out why "print self.gramchunk" gives an error
            self.gramchunk = GramNChunk(self)
            self.gramchunk.add_verb_features(verbGramFeat)
            logger.debug(self.gramchunk.as_extended_string())
            # Even if preceded by a BE or a HAVE form, only tagging N Chunks headed by an
            # eventive noun E.g., "was an intern" will NOT be tagged
            if self.gramchunk.isEventCandidate():
                logger.debug("Nominal is an event candidate")
                self._processEventInChunk()


class VerbChunk(Chunk):

    def __init__(self, phraseType):
        Chunk.__init__(self, phraseType)
        self.verbs = [-1,-1]

    def getVerbs(self):
        return self.dtrs[self.verbs[0]:self.verbs[1]]

    def startVerbs(self):
        self.verbs[0] = len(self.dtrs)

    def endVerbs(self):
        self.verbs[1] = len(self.dtrs) -1

    def isVerbChunk(self):
        return 1

    def _updatePositionInSentence(self, endPosition):
        pass

    # The following methods are all from the Evita version. Slinket threw an error when
    # all methods were included, the culprit being _identify_substring, which overrides a
    # slightly different method on Chunk and introduces an error, and whose name was
    # changed a bit for the slinket/s2t version. Need to find better solution.
    # NOTE: this comment may be obsolete by now

    def XXX_identify_substring(self, sentence_slice, fsa_list):
        """Almost the same as Chunk._identify_substring, except that the fsa
        method called is acceptSubstringOf. Method may be obsolete."""
        fsaCounter = -1 
        for fsa in fsa_list:
            #logger.out('Trying FSA', fsa.fsaname)
            fsaCounter += 1
            logger.debug(str(fsa))
            lenSubstring = fsa.acceptsSubstringOf(sentence_slice)
            ##logger.out('length of found match', lenSubstring)
            if lenSubstring:
                return (lenSubstring, fsaCounter)
        else:
            return (0, fsaCounter)

    def _updateFlagCheckedForEvents(self, multiChunkEnd):
        """Update Position in sentence, by marking as already checked for EVENT
        upcoming Tokens and Chunks that are included in multi-chunk """
        for item in multiChunkEnd:
            item.setFlagCheckedForEvents()
            
    def _getRestSent(self, structure):
        """Obtaining the rest of the sentence, which can be
        in a flat, token-based structure, or chunked."""
        logger.debug("Entering _getRestSent")
        if structure == 'flat':
            restSentence = self.getTokens(self.parent[self.position+1:])
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
        GramMultiVChunk = GramVChunkList(self._createMultiChunk(substring))[0] 
        self._processEventInChunk(GramMultiVChunk)
        self._updateFlagCheckedForEvents(substring)

    def _processEventInMultiNChunk(self, GramVCh, substring):
        nounChunk = substring[-1]
        verbGramFeatures = {'tense': GramVCh.tense,
                            'aspect': GramVCh.aspect,
                            'modality': GramVCh.modality,
                            'polarity': GramVCh.polarity}
        nounChunk.createEvent(verbGramFeatures)
        self._updateFlagCheckedForEvents(substring)

    def _processEventInMultiAChunk(self, GramVCh, substring):
        adjToken = substring[-1]
        verbGramFeatures = {'tense': GramVCh.tense,
                            'aspect': GramVCh.aspect,
                            'modality': GramVCh.modality,
                            'polarity': GramVCh.polarity}
        adjToken.createAdjEvent(verbGramFeatures)
        self._updateFlagCheckedForEvents(substring)

    def _processDoubleEventInMultiAChunk(self, GramVCh, substring):
        """Tagging EVENT in VChunk """
        logger.debug("[V_2Ev] " + GramVCh.as_extended_string())
        self._processEventInChunk(GramVCh)
        """Tagging EVENT in AdjToken"""
        adjToken = substring[-1]
        adjToken.createAdjEvent()
        self._updateFlagCheckedForEvents(substring)

        
    def _createEventOnRightmostVerb(self, GramVCh):

        if GramVCh.nodeIsNotEventCandidate():
            return

        if GramVCh.nodeIsModalForm(self.nextNode()):
            logger.debug("Entering checking for modal pattern............")
            substring = self._lookForMultiChunk(patterns.MODAL_FSAs)
            if substring:
                self._processEventInMultiVChunk(substring)

        elif GramVCh.nodeIsBeForm(self.nextNode()):
            logger.debug("Entering checking for toBe pattern............")
            """Looking for BE + NOM Predicative Complement """
            logger.debug("Looking for BE + NOM Predicative Complement ")
            substring = self._lookForMultiChunk(patterns.BE_N_FSAs, 'chunked')
            if substring:
                self._processEventInMultiNChunk(GramVCh, substring)  
            else:
                """Looking for BE + ADJ Predicative Complement """
                logger.debug("Looking for BE + ADJ Predicative Complement ")
                substring = self._lookForMultiChunk(patterns.BE_A_FSAs, 'chunked')
                if substring:
                    self._processEventInMultiAChunk(GramVCh, substring)  
                else:
                    """Looking for BE + additional VERBAL structure """
                    logger.debug("Looking for BE + VERB Predicative Complement ")
                    substring = self._lookForMultiChunk(patterns.BE_FSAs)
                    if substring:
                        self._processEventInMultiVChunk(substring)
                       
        elif GramVCh.nodeIsHaveForm():
            logger.debug("Entering checking for toHave pattern............")
            substring = self._lookForMultiChunk(patterns.HAVE_FSAs)
            if substring:
                self._processEventInMultiVChunk(substring)
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsFutureGoingTo():
            logger.debug("Entering checking for futureGoingTo pattern............")
            substring = self._lookForMultiChunk(patterns.GOINGto_FSAs)
            if substring:
                self._processEventInMultiVChunk(substring)
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsPastUsedTo():
            logger.debug("Entering checking for pastUsedTo pattern............")
            substring = self._lookForMultiChunk(patterns.USEDto_FSAs)
            if substring:
                self._processEventInMultiVChunk(substring)
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsDoAuxiliar():
            logger.debug("Entering checking for doAuxiliar pattern............")
            substring = self._lookForMultiChunk(patterns.DO_FSAs)
            if substring:
                self._processEventInMultiVChunk(substring)
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsBecomeForm(self.nextNode()):
            """Looking for BECOME + ADJ Predicative Complement e.g., He became famous at
            the age of 21"""
            logger.debug("Looking for BECOME + ADJ")
            substring = self._lookForMultiChunk(patterns.BECOME_A_FSAs, 'chunked')
            if substring:
                logger.debug("BECOME + ADJ found")
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsContinueForm(self.nextNode()):
            """Looking for CONTINUE + ADJ Predicative Complement e.g., Interest rate
            continued low."""
            logger.debug("Looking for CONTINUE + ADJ")
            substring = self._lookForMultiChunk(patterns.CONTINUE_A_FSAs, 'chunked')
            if substring:
                logger.debug("CONTINUE + ADJ found")
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self._processEventInChunk(GramVCh)

        elif GramVCh.nodeIsKeepForm(self.nextNode()):
            """Looking for KEEP + ADJ Predicative Complement e.g., The announcement kept
            everybody Adj."""
            logger.debug("Looking for KEEP + [NChunk] + ADJ ")
            substring = self._lookForMultiChunk(patterns.KEEP_A_FSAs, 'chunked')
            if substring:
                logger.debug("KEEP + ADJ found")
                self._processDoubleEventInMultiAChunk(GramVCh, substring)  
            else:
                self._processEventInChunk(GramVCh)
            
        else:
            logger.debug("[1] " + GramVCh.as_extended_string())
            self._processEventInChunk(GramVCh)

            
    def createEvent(self):
        """Try to create an event in the VerbChunk. Delegates to two methods
        depending on the position of the verb in the chunk."""

        logger.debug("VerbChunk.createEvent()")
        GramVChList = GramVChunkList(self)
        if GramVChList.do_not_process():
            return
        logger.debug(GramVChList[-1].as_extended_string())
        logger.debug("len(GramVChList) ==> %d" % len(GramVChList))

        # simple case
        if len(GramVChList) == 1:
            self._createEventOnRightmostVerb(GramVChList[-1])
        # complex case
        else:
            lastIdx = len(GramVChList) - 1
            for idx in range(len(GramVChList)):
                gramVCh = GramVChList[idx]
                if idx == lastIdx:
                    self._createEventOnRightmostVerb(gramVCh)
                else:
                    logger.debug("[Not Last] " + gramVCh.as_extended_string())
                    if not gramVCh.isAuxVerb():
                        self._processEventInChunk(gramVCh)

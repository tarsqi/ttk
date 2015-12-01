from types import ListType, StringType, TupleType

from utilities import logger
from library.timeMLspec import EVENT_INSTANCE_ID
from library.timeMLspec import SUBORDINATED_EVENT_INSTANCE
from library.timeMLspec import RELATED_TO_EVENT_INSTANCE
from library.timeMLspec import ALINK, SLINK, SYNTAX, RELTYPE


class Constituent:
    """An abstract class that contains some methods that are identical for Chunks and
    Tokens plus a couple of default methods."""

    def setParent(self, parent):
        self.parent = parent
        self.position = parent.positionCount

    def doc(self):
        return self.document()

    def document(self):
        return self.parent.document()

    def isToken(self): return False
    def isAdjToken(self): return False
    def isChunk(self): return False
    def isVerbChunk(self): return False
    def isNounChunk(self): return False
    def isAdjChunk(self): return False
    def isTimex(self): return False
    def isEvent(self): return False
    def isNChHead(self): return False
    def isPreposition(self): return False
    
    def __getattr__(self, name):
        """Used by node._matchChunk. Needs cases for all instance variables used in the
        pattern matching phase."""
        if name == 'nodeType':
            return self.__class__.__name__
        elif name == 'text':
            return None
        elif name == 'pos':
            return None        
        else:
            raise AttributeError, name

    def setCheckedEvents(self):
        if self.parent.__class__.__name__ == 'Sentence':
            self.checkedEvents = True
        else:
            self.parent.setCheckedEvents()

    def getText(self):
        logger.warn("Unexpected recipient of getText")

    def nextNode(self):
        """Return the right sibling in the tree or None if there is none. Works nicely
        when called on Sentence elements. If called on the last token in a chunk, then
        it returns None even if there is another chunk following."""
        # TODO: make this work for tokens as well, maybe by adding this method to Token
        try:
            return self.parent[self.position+1]
        except IndexError:
            return None

    def createEvent(self, tarsqidoc):
        """Does nothing except for logging a warning. If this happens something weird is
        going on. Event creation is only attempted on some sub classes."""
        logger.warn("Unexpected recipient of createEvent()")

    def _hackToSolveProblemsInValue(self, value):
        """From slinket/s2t"""
        #logger.out('self is a', self.__class__.__name__, '; value =', value)
        if type(value) is ListType:
            if len(value) == 2 and value[0] == '' and value[1] == '':
                return [',']
            else:
                return value
        elif type(value) is StringType:
            if value == '':
                return '"'
            else:
                return value
        else:
            return value

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
    
        This method is also implemented in the chunkAnalyzer.GramChunk class and
        the Chunk class"""

        logger.debug(str(chunkDescription))
        for feat in chunkDescription.keys():
            value = chunkDescription[feat]
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
                    return 0
            else:
                value = self._hackToSolveProblemsInValue(value)
                if self.__getattr__(feat) != value:
                    return 0
        return 1


    def get_event(self):
        """Return None or the EventTag that is contained in the constituent."""
        if self.isEvent():
            return self
        elif self.isChunk:
            for element in self:
                if element.isEvent():
                    return element
        return None

    def get_timex(self):
        """Return None or the TimexTag that is contained in the constituent."""
        if self.isTimex():
            return self
        elif self.isChunk:
            for element in self:
                if element.isTimex():
                    return element
        return None

    def pp(self):
        self.pretty_print()

    def pretty_print(self):
        print "<<pretty_print() not defined for this object>>"



    # SLINKET METHODS
    
    # There is some serious redundancy here, refactor these methods.

        
    def find_forward_alink(self, fsa_reltype_groups):

        """Search for an alink to the right of the event. Return True
        is event was found, False otherwise."""

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        alinkedEventContext = self.parent[self.position+1:]
        return self._find_alink(alinkedEventContext, fsa_lists, reltypes_list)

    
    def find_backward_alink(self, fsa_reltype_groups):

        """Search for an alink to the left of the event. Return True is event was found,
        False otherwise. Note that the context includes the event itself and the token to
        its immediate right. It is not quite clear why but it has tro do with how the
        patterns are defined.

        Backward Alinks also check for the adequacy (e.g., in terms of TENSE or ASPECT) of
        the Subordinating Event. For cases such as 'the <EVENT>transaction</EVENT> has
        been <EVENT>completed</EVENT>'"""

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        alinkedEventContext = self.parent[:self.position+1]
        alinkedEventContext.reverse()
        return self._find_alink(alinkedEventContext, fsa_lists, reltypes_list)


    def _find_alink(self, event_context, fsa_lists, reltype_list):

        """Try to create an alink using the context and patterns from the
        dictionary. Alinks are created as a side effect. Returns True if an alink was
        created, False otherwise."""
       
        for i in range(len(fsa_lists)):

            fsa_list = fsa_lists[i]
            result = self._look_for_link(event_context, fsa_lists[i])
            if result:
                (length_of_match, fsa_num) = result
                fsa = fsa_list[fsa_num]
                #logger.debug("match found, FSA=%s size=%d reltype=%s"
                #           % (fsa.fsaname, length_of_match, reltype))
                reltype = get_reltype(reltype_list, i)
                eiid = event_context[length_of_match-1].eiid
                alinkAttrs = {
                    EVENT_INSTANCE_ID: self.eiid, 
                    RELATED_TO_EVENT_INSTANCE: eiid,
                    RELTYPE: reltype,
                    SYNTAX: fsa.fsaname }
                self.document().addLink(alinkAttrs, ALINK)
                logger.debug("ALINK CREATED")
                return True
            else:
                logger.debug("REJECTED ALINK by FSA: "+str(i))  

        return False
    

    def find_forward_slink(self, fsa_reltype_groups):

        """Tries to create forward Slinks, using a group of FSAs.

        Arguments:
           fsa_reltype_groups -
               a list of two lists, the first list is a list of fsa
               lists, the second list is a list of relation types
               [ [ [fsa, fsa, ...], [fsa, fsa, ...], ...],
                 [ reltype, reltype, ... ] ] """

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        event_context = self.parent[self.position+1:]
        return self._find_slink(event_context, fsa_lists, reltypes_list) 


    def find_backward_slink(self, fsa_reltype_groups):

        """Tries to create backward Slinks, using a group of FSAs.  Backward Slinks should
        check for the adequacy (e.g., in terms of TENSE or ASPECT) of the Subordinating
        Event. For cases such as 'the <EVENT>transaction</EVENT> has been
        <EVENT>approved</EVENT>'

        Arguments:
           fsa_reltype_groups - see createForwardSlinks """

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        event_context = self.parent[:self.position+1]
        event_context.reverse()
        return self._find_slink(event_context, fsa_lists, reltypes_list) 


    def find_reporting_slink(self, fsa_reltype_groups):

        """Reporting Slinks are applied to reporting predicates ('say', 'told', etc) that
        link an event in a preceeding quoted sentence which is separated from the clause
        of the reporting event by a comma; e.g.,

            ``I <EVENT>want</EVENT> a referendum,'' Howard
            <EVENT class='REPORTING'>said</EVENT>.

        Slinket assumes that these quoted clauses always initiate the main
        sentence. Therefore, the first item in the sentence are quotation marks."""

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        sentenceBeginning = self.parent[:self.position]
        if len(sentenceBeginning) > 0 and sentenceBeginning[0].getText() == "``":
            #quotation does not contain quotation marks
            quotation = self._extract_quotation(sentenceBeginning)
            if quotation is not None:
                logger.debug("TRYING reporting slink")
                return self._find_slink(quotation, fsa_lists, reltypes_list)
        return False
    

    def _find_slink(self, event_context, fsa_lists, reltype_list):

        """Try to find an slink in the given event_context using lists of FSAs. If the
        context matches an FSA, then create an slink and insert it in the document.""" 
            
        for i in range(len(fsa_lists)):

            fsa_list = fsa_lists[i]
            result = self._look_for_link(event_context, fsa_list)
            if result:
                (length_of_match, fsa_num) = result
                fsa = fsa_list[fsa_num]
                #logger.debug("match found, FSA=%s size=%d reltype=%s"
                #           % (fsa.fsaname, length_of_match, reltype))
                reltype = get_reltype(reltype_list, i)
                eiid = event_context[length_of_match-1].eiid
                slinkAttrs = {
                    EVENT_INSTANCE_ID: self.eiid,
                    SUBORDINATED_EVENT_INSTANCE: eiid,
                    RELTYPE: reltype,
                    SYNTAX: fsa.fsaname }
                self.doc().addLink(slinkAttrs, SLINK)
                logger.debug("SLINK CREATED")
                return True
            else:
                logger.debug("REJECTED SLINK by FSA: "+str(i))
                
        return False


    def _look_for_link(self, sentence_slice, fsa_list):

        """Given a slice of a sentence and a list of FSAs, return a tuple of the size of
        the matching slize and the number of the FSA that featured in the match. Return
        False if there is no match."""

        # Eventually, if we want to merge EVITA and SLINKET common stuff, this method
        # should call self._lookForStructuralPattern(FSA_set) But careful: _lookForLink
        # MUST return also fsaNum and that will have effects on Evita code.

        lenSubstring, fsaNum = self._identify_substring(sentence_slice, fsa_list)
        #print fsa_list[0]
        #print "\nSENTENCE_SLICE"
        #for sl in sentence_slice: sl.pp()
            
        if lenSubstring: 
            return (lenSubstring, fsaNum)
        else:
            return False


    def _identify_substring(self, sentence_slice, fsa_list):

        """Checks whether a token sequnce matches an pattern. Returns a tuple of the sub
        sequence length that matched the pattern (where a zero length indicates
        no match) and the index of the FSA that returned the match. This is the
        method where the FSA is asked to find a substring in the sequence that
        matches the FSA.

        Arguments:
           sentence_slice - a list of Chunks and Tokens
           fsa_list - a list of FSAs

        """

        fsaCounter = -1 
        for fsa in fsa_list:
            fsaCounter += 1
            lenSubstring = fsa.acceptsShortestSubstringOf(sentence_slice)
            if lenSubstring:
                return (lenSubstring, fsaCounter)
        return (0, fsaCounter)

        
    def _extract_quotation(self, fragment):
        for idx in range(len(fragment)):
            try:
                # For some reason, it may break here (though rarely)
                if (fragment[idx].getText() == "''" and
                    (fragment[idx-1].getText() == "," or
                     fragment[idx+1].getText() == ",")):
                    return fragment[1:idx]
            except:
                logger.warn('Quotation could not be extracted')
        else:
            return
        
        
def get_reltype(reltype_list, i):
    """Returns the reltype in reltype_list at index i. Returns the last element of reltype
    list if i is out of bounds (which happens when patterns have a list of reltypes that
    is shorter than the list of FSAs."""
    try:
        reltype = reltype_list[i]
    except IndexError:
        reltype = reltype_list[-1]
    return reltype

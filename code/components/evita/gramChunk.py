"""

This module contains classes that add grammatical features to NounChunks,
VerbChunks and AdjectiveTokens. The grammatical features drive part of the event
recognition.

It is debatable whether the functionality should be here or whether it should be
on the classes that these classes are attached to. This module feels like a bit
of a hodge-podge and the naming of the classes (GramNChunk etcetera) is a bit
unfortunate and tends to be confusing.

Included here is functionality to:
- look up nominals in WordNet (using wordnet module)
- run a simple bayesian classifier
- check whether a nominal is a potential event
- check the kind of verb chunk (modal, future)
- generate the event class

"""

from types import ListType, InstanceType

import wordnet
from rule import FeatureRule
from bayes import BayesEventRecognizer
from bayes import DisambiguationError

import utilities.porterstemmer as porterstemmer
import utilities.logger as logger
from utilities.file import open_pickle_file

from library import forms
from library.evita.patterns.feature_rules import FEATURE_RULES

DEBUG = False

# Determines whether we try to disambiguate nominals with training data
NOM_DISAMB = True

# Determines whether we use context information in training data (has no effect if
# NOM_DISAMB == False).
NOM_CONTEXT = True

# Determines how we use WordNet to recognize events. If True, mark only forms
# whose first WN sense is an event sense, if False, mark forms which have any
# event sense (if NOM_DISAMB is true, this is only a fallback where no training
# data exists).
NOM_WNPRIMSENSE_ONLY = True


# Open pickle files with semcor and verbstem information
DictSemcorEvent = open_pickle_file(forms.DictSemcorEventPickleFilename)
DictSemcorContext = open_pickle_file(forms.DictSemcorContextPickleFilename)
DictVerbStems = open_pickle_file(forms.DictVerbStemPickleFileName)

# Create the Bayesian event recognizer and the stemmer
nomEventRec = BayesEventRecognizer(DictSemcorEvent, DictSemcorContext)
stemmer = porterstemmer.Stemmer()

if DEBUG:
    print "NOM_DISAMB = %s" % NOM_DISAMB
    print "NOM_CONTEXT = %s" % NOM_CONTEXT
    print "NOM_WNPRIMSENSE_ONLY = %s" % NOM_WNPRIMSENSE_ONLY
    print "DBM_FILES_OPENED = %s" % DBM_FILES_OPENED


def getWordList(constituents):
    """Returns a list of words from the list of constituents, typically the
    constituents are instances of NounChunk, VerbChunk or Token. Used for
    debugging purposes."""
    return [constituent.getText() for constituent in constituents]

def getPOSList(constituents):
    """Returns a list of parts-of-speech from the list of constituents, typically
    the constituents are instances of NounChunk, VerbChunk or Token. Used for
    debugging purposes."""
    return [constituent.pos for constituent in constituents]

def remove_timex_nodes(nodes):
    """Take a list of nodes and flatten it out by removing Timex tags."""
    return_nodes = []
    for node in nodes:
        if node.isTimex():
            for tok in node:
                return_nodes.append(tok)
        else:
            return_nodes.append(node)
    return return_nodes

def debug(*args):
    if DEBUG:
        for arg in args: print arg,
        print

        
class GramChunk:

    """The subclasses of this class are used to add grammatical features to a
    NounChunk, VerbChunk or AdjectiveToken. It lives in the gramchunk variable
    of instances of those classes."""

    def __init__(self, chunk_or_token):
        """Common initialization for GramNChunk and GramAChunk."""
        self.node = chunk_or_token
        self.tense = "NONE"
        self.aspect = "NONE"
        self.modality = "NONE"
        self.polarity = "POS"

    def check_class(self, class_name):
        node_class_name = self.node.__class__.__name__
        if node_class_name == class_name:
            logger.warn("%s created with instance of %s" %
                        (self.__class__.__name__, node_class_name))

    def add_verb_features(self, gramvchunk):
        """Set grammatical features (tense, aspect, modality and polarity) with the
        features handed in from the governing verb."""
        if gramvchunk is not None:
            self.tense = gramvchunk.tense
            self.aspect = gramvchunk.aspect
            self.modality = gramvchunk.modality
            self.polarity = gramvchunk.polarity

    def as_verbose_string(self):
        """Debugging method to print the GramChunk and its features."""
        return \
            "%s: %s\n" % (self.__class__.__name__, self.node.getText()) + \
            "\tTENSE=%s ASPECT=%s HEAD=%s CLASS=%s\n" \
            % (self.tense, self.aspect, self.head.getText(), self.evClass) + \
            "\tNF_MORPH=%s MODALITY=%s POLARITY=%s\n" \
            % (self.nf_morph, self.modality, self.polarity) + \
            "\tHEAD=%s CLASS=%s\n" % (self.head.getText(), self.evClass)


class GramAChunk(GramChunk):

    """Contains the grammatical features for an AdjectiveToken."""

    def __init__(self, adjectivetoken):
        """Initialize with an AdjectiveToken and use default values for most instance
        variables, but percolate grammatical features from the copular verb if
        they were handed in."""
        GramChunk.__init__(self, adjectivetoken)
        self.check_class('AdjectiveToken')
        self.nf_morph = "ADJECTIVE"
        self.head = adjectivetoken
        self.evClass = self.getEventClass()

    def getEventClass(self):
        """Return I_STATE if the head is on a short list of intentional state
        adjectives, return STATE otherwise."""
        headString = self.head.getText()
        return 'I_STATE' if headString in forms.istateAdj else 'STATE'


class GramNChunk(GramChunk):

    """Contains the grammatical features for a NounChunk."""

    def __init__(self, nounchunk):
        """Initialize with a NounChunk and use default values for most instance
        variables."""
        GramChunk.__init__(self, nounchunk)
        self.check_class('NounChunk')
        self.nf_morph = "NOUN"
        self.head = self.node.getHead()
        self.evClass = self.getEventClass()

    def getEventClass(self):
        """Get the event class for the GramChunk. For nominals, the event class
        is always OCCURRENCE."""
        return "OCCURRENCE"
  
    def getEventLemma(self):
        """Return the lemma from the head of the GramNChunk. If there is no head
        or the head has no lemma, then build it from the text using a stemmer."""
        try:
            return self.head.lemma
        except AttributeError:
            return stemmer.stem(self.head.getText().lower())

    def isEventCandidate(self):
        """Return True if the nominal is syntactically and semantically an
        event, return False otherwise."""
        return self.isEventCandidate_Syn() and self.isEventCandidate_Sem()

    def isEventCandidate_Syn(self):
        """Return True if the GramNChunk is syntactically able to be an event,
        return False otherwise. An event candidate syntactically has to have a
        head (which cannot be a timex) and the head has to be a common noun."""
        if self.head.isTimex():
            return False
        # using the regular expression is a bit faster then lookup in the short
        # list of common noun parts of speech (forms.nounsCommon)
        return self.head and forms.RE_nounsCommon.match(self.head.pos)

    def isEventCandidate_Sem(self):
        """Return True if the GramNChunk can be an event semantically. Depending
        on user settings this is done by a mixture of wordnet lookup and using a
        simple classifier."""
        debug("event candidate?")
        lemma = self.getEventLemma()
        # return True if all WorrdNetsenses are events, no classifier needed
        if wordnet.allSensesAreEvents(lemma):
            return True
        # run the classifier if required, fall through on disambiguation error
        if NOM_DISAMB:
            try:
                return self._run_classifier(lemma)
            except DisambiguationError, (strerror):
                debug("  DisambiguationError: %s" % unicode(strerror))
        # check whether primary sense or some of the senses are events
        if NOM_WNPRIMSENSE_ONLY:
            is_event = wordnet.primarySenseIsEvent(lemma)
            debug("  primary WordNet sense is event ==> %s" % is_event)
        else:
            is_event = wordnet.someSensesAreEvents(lemma)
            debug("  some WordNet sense is event ==> %s" % is_event)
        return is_event

    def _run_classifier(self, lemma):
        """Run the classifier on lemma, using features from the GramNChunk."""
        features = []
        if NOM_CONTEXT:
            features = ['DEF' if self.node.isDefinite() else 'INDEF', self.head.pos]
        is_event = nomEventRec.isEvent(lemma, features)
        debug("  nomEventRec.isEvent(%s) ==> %s" % (lemma, is_event))
        return is_event


class GramVChunkList:

    def __init__(self, node):
        self.node = node
        self.counter = 0 # To control different subchunks w/in a chunk (e.g., "began to study") 
        self.gramVChunksList = []
        self.trueChunkLists = [[]]
        self.negMarksLists = [[]]
        self.infMarkLists = [[]]
        self.adverbsPreLists = [[]]
        self.adverbsPostLists = [[]]
        self.leftLists = [[]]
        self.chunkLists = [self.trueChunkLists, self.negMarksLists, self.infMarkLists,
                           self.adverbsPreLists, self.adverbsPostLists, self.leftLists]
        self.distributeInfo()
        self.generateGramVChunks() 

    def __len__(self):
        return len(self.gramVChunksList)

    def __getitem__(self, index):
        return self.gramVChunksList[index]

    def __str__(self):
        if len(self.gramVChunksList) == 0:
            return '[]'
        string = ''
        for i in self.gramVChunksList:
            node = "\n\tNEGATIVE: " + str(getWordList(i.negMarks)) \
                + "\n\tINFINITIVE: "  + str(getWordList(i.infMark)) \
                + "\n\tADVERBS-pre: " + str(getWordList(i.adverbsPre)) \
                + "\n\tADVERBS-post: %s%s" % (getWordList(i.adverbsPost), getPOSList(i.adverbsPost)) \
                + "\n\tTRUE CHUNK: %s%s" % (getWordList(i.trueChunk), getPOSList(i.trueChunk)) \
                + "\n\tTENSE: " + str(i.tense) \
                + "\n\tASPECT: " + str(i.aspect) \
                + "\n\tNF_MORPH: " + str(i.nf_morph) \
                + "\n\tMODALITY: " + str(i.modality) \
                + "\n\tPOLARITY: " + str(i.polarity) \
                + "\n\tHEAD: " + str(i.head.getText()) \
                + "\n\tCLASS: " + str(i.evClass) + "\n"
            string += node
        return string

    def do_not_process(self):
        """Return True if this GramVChunkList can be skipped, either because
        there are no true chunks or because there is no content."""
        true_chunks = self.trueChunkLists
        if len(true_chunks) == 1 and not true_chunks[0]:
            return True
        if len(self) == 0:
            logger.warn("Obtaining an empty GramVChList")
            return True
        return False

    def distributeInfo(self):
        tempNodes = self.remove_interjections()
        tempNodes = remove_timex_nodes(tempNodes)
        itemCounter = 0
        for item in tempNodes:
            if item.pos == 'TO':
                if itemCounter != 0:
                    try:
                        if self.trueChunkLists[-1][-1].getText() \
                                in ['going', 'used', 'has', 'had', 'have', 'having']:
                            self.addInCurrentSublist(self.trueChunkLists, item)
                    except: pass
                else:
                    self.addInCurrentSublist(self.infMarkLists, item)
            elif item.getText() in forms.negative:
                self.addInCurrentSublist(self.negMarksLists, item)
            elif item.pos == 'MD':
                self.addInCurrentSublist(self.trueChunkLists, item)
            elif item.pos[0] == 'V':
                if item == tempNodes[-1]:
                    self._treatMainVerb(item, tempNodes, itemCounter)
                elif (item.isMainVerb() and
                      not item.getText() in ['going', 'used', 'had', 'has', 'have', 'having']):
                    self._treatMainVerb(item, tempNodes, itemCounter)
                elif (item.isMainVerb() and
                      item.getText() in ['going', 'used', 'had', 'has', 'have', 'having']):
                    try:
                        if (tempNodes[itemCounter+1].getText() == 'to' or
                            tempNodes[itemCounter+2].getText() == 'to'):
                            self.addInCurrentSublist(self.trueChunkLists, item)
                        else:
                            self._treatMainVerb(item, tempNodes, itemCounter)
                    except:
                        self._treatMainVerb(item, tempNodes, itemCounter)
                else:
                    self.addInCurrentSublist(self.trueChunkLists, item)
            elif item.pos in forms.partAdv:
                if item != tempNodes[-1]:
                    if len(tempNodes) > itemCounter+1:
                        if (tempNodes[itemCounter+1].pos == 'TO' or
                            self.isFollowedByOnlyAdvs(tempNodes[itemCounter:])):
                            self.addInPreviousSublist(self.adverbsPostLists, item)
                        else:
                            self.addInCurrentSublist(self.adverbsPreLists, item)
                    else:
                        self.addInCurrentSublist(self.adverbsPostLists, item)
                else:
                    self.addInPreviousSublist(self.adverbsPostLists, item)
            itemCounter += 1

    def _treatMainVerb(self, item, tempNode, itemCounter):
        self.addInCurrentSublist(self.trueChunkLists, item)
        self.updateCounter()
        if (item == tempNode[-1] or
            self.isFollowedByOnlyAdvs(tempNode[itemCounter+1:])):
            pass
        else:
            self.updateChunkLists()

    def isFollowedByOnlyAdvs(self, sequence):
        non_advs = [item for item in sequence if item.pos not in forms.partInVChunks2]
        return False if non_advs else True

    def remove_interjections(self):
        """Remove interjections and punctuations from inside a sequence of
        tokens. Examples:
        - ['ah', ',', 'coming', 'up']  >> ['ah', 'coming', 'up']
        - ['she', 'has', ',',  'I', 'think', ',', 'to', 'go'] >> ['she', 'has', 'to', 'go']"""
        # TODO. In the 6000 tokens of evita-test2.xml, this applies only once,
        # replacing 'has, I think, been' with 'has been', but that seems like an
        # error because the input had an extra verb after 'been' ('has, I think,
        # been demolished'). Could perhaps remove this method. Also, it is a bit
        # peculiar how 'has, I think, been' ends up as a sequence, find out why.
        before = []  # nodes before first punctuation
        after = []   # nodes after last punctuation
        for item in self.node:
            if item.pos not in (',', '"', '``'):
                before.append(item)
            else: break
        for item in reversed(self.node):
            if item.pos not in (',', '"', '``'):
                after.insert(0, item)
            else: break
        if len(before) == len(after) == len(self.node):
            # no punctuations or interjections
            return before
        elif len(before) + len(after) == len(self.node) - 1:
            # one punctuation
            return before + after
        else:
            # two punctuations with potential interjection
            return before + after

    def updateCounter(self):
        self.counter += 1

    def getNodeName(self):
        if type(self.node) is InstanceType:
            # Node is a Chunk from chunked input
            return self.node.phraseType
        elif type(self.node) is ListType:
            # Node is a sequence of chunks and/or tokens (i.e., multi-chunk)
            return 'VMX'
        else:
            # Node is the head element
            return "VH"

    def updateChunkLists(self):
        """Necessary for dealing with chunks containing subchunks e.g., 'remains to be
        seen'."""
        for list in self.chunkLists:
            if len(list) == self.counter:
                # The presence of a main verb has already updated self.counter
                list.append([])

    def addInCurrentSublist(self, tokens, element):
        if len(tokens) - self.counter == 1:
            tokens[self.counter].append(element)
        else:
            # The presence of a main verb has already updated self.counter
            pass

    def addInPreviousSublist(self, tokens, element):
        if len(tokens) == 0 and self.counter == 0:
            tokens.append([element])
        elif len(tokens) >= self.counter-1:
            tokens[self.counter-1].append(element)
        else:
            logger.warn("list should be longer")

    def generateGramVChunks(self):
        self.normalizeLists()
        lenLists = len(self.trueChunkLists)
        for idx in range(lenLists):
            gramVCh = GramVChunk(self.node,
                                 self.trueChunkLists[idx],
                                 self.negMarksLists[idx],
                                 self.infMarkLists[idx],
                                 self.adverbsPreLists[idx],
                                 self.adverbsPostLists[idx],
                                 self.leftLists[idx])
            self.gramVChunksList.append(gramVCh)

    def normalizeLists(self):
        for idx in range(len(self.chunkLists)-1):
            if len(self.chunkLists[idx]) < len(self.chunkLists[idx+1]):
                self.chunkLists[idx].append([])
            elif len(self.chunkLists[idx]) > len(self.chunkLists[idx+1]):
                self.chunkLists[idx+1].append([])

            
class GramVChunk(GramChunk):

    def __init__(self, verbchunk, tCh, negMk, infMk, advPre, advPost, left):
        self.node = verbchunk
        self.trueChunk = tCh  
        self.negMarks = negMk  
        self.infMark = infMk  
        self.adverbsPre = advPre  
        self.adverbsPost = advPost  
        self.left = left  
        self.negative = self.negMarks
        self.infinitive = self.infMark
        self.tense = 'NONE'
        self.aspect = 'NONE'
        self.nf_morph = 'VERB'
        self.set_tense_and_aspect()
        self.modality = self.getModality()
        self.polarity = self.getPolarity()
        self.head = self.getHead()
        self.evClass = self.getEventClass()
        # the following four are added so that the pattern matcher can access
        # these embedded variables directly
        self.headForm = self.head.getText()
        self.headPos = self.head.pos
        self.preHead = self.getPreHead()
        self.preHeadForm = self.preHead.getText() if self.preHead else ''

    def __str__(self):
        return \
            "<GramVChunk>\n" + \
            "\thead         = %s\n" % ( str(self.head) ) + \
            "\tevClass      = %s\n" % ( str(self.evClass) ) + \
            "\ttense        = %s\n" % ( str(self.tense) ) + \
            "\taspect       = %s\n" % ( str(self.aspect) )

    def isAuxVerb(self):
        return True if self.head.getText().lower() in forms.auxVerbs else False

    def getHead(self):
        if self.trueChunk:
            return self.trueChunk[-1]
        else:
            debug("WARNING: empty trueChunk, head is set to None")
            return None

    def getPreHead(self):
        if self.trueChunk and len(self.trueChunk) > 1:
            return  self.trueChunk[-2]
        else:
            return None

    def set_tense_and_aspect(self):
        """Sets the tense and aspect attributes by overwriting the default values with
        results from the feature rules in FEATURE_RULES. This method also tries a trick
        in case no features were extracted from the rules."""
        # TODO: get to understand that trick
        features = self.apply_feature_rules()
        if features is not None:
            (tense, aspect, nf_morph) = features
            self.tense = tense
            self.aspect = aspect
        elif len(self.trueChunk) > 1 and self.head is not None:
            self.tense = getattr(GramVChunkList([self.head])[0], 'tense')
            self.aspect = getattr(GramVChunkList([self.head])[0], 'aspect')

    def apply_feature_rules(self):
        """Returns a triple of TENSE, ASPECT and CATEGORY given the tokens of the chunk,
        which are stored in self.trueChunk. Selects the rules relevant for the
        length of the chunk and applies them. Returns None if no rule applies."""
        rules = FEATURE_RULES[len(self.trueChunk)]
        for rule in rules:
            features = FeatureRule(rule, self.trueChunk).match()
            if features:
                return features
        return None

    def getModality(self):
        modal = ''
        for i in range(len(self.trueChunk)):
            item = self.trueChunk[i]
            if (item.pos == 'MD' and
                item.getText() in forms.allMod):
                logger.debug("MODALity...... 1")
                if item.getText() in forms.wholeMod:
                    modal = modal+' '+item.getText()
                else:
                    modal = modal+' '+self.normalizeMod(item.getText())
            elif (item.getText() in forms.have and
                  i+1 < len(self.trueChunk) and
                  self.trueChunk[i+1].pos == 'TO'):
                logger.debug("MODALity...... 2")
                if item.getText() in forms.wholeHave:
                    modal = modal+' have to'
                else:
                    modal = modal+' '+self.normalizeHave(item.getText())+' to' 
        return modal.strip() if modal else 'NONE'

    def nodeIsNotEventCandidate(self):
        """Return True if the GramVChunk cannot possibly be an event. This is the place
        for performing some simple stoplist-like tests."""
        # TODO: why would any of these ever occur?
        # TODO: if we use a stop list it should be separated from the code
        return ((self.headForm == 'including' and self.tense == 'NONE')
                or self.headForm == '_')

    def nodeIsModalForm(self, nextNode):
        return self.headPos == 'MD' and nextNode

    def nodeIsBeForm(self, nextNode):
        return self.headForm in forms.be and nextNode

    def nodeIsBecomeForm(self, nextNode):
        return self.headForm in forms.become and nextNode

    def nodeIsContinueForm(self, nextNode):
        return forms.RE_continue.match(self.headForm) and nextNode

    def nodeIsKeepForm(self, nextNode):
        return forms.RE_keep.match(self.headForm) and nextNode

    def nodeIsHaveForm(self):
        return self.headForm in forms.have and self.headPos is not 'MD'

    def nodeIsFutureGoingTo(self):
        return len(self.trueChunk) > 1 \
            and self.headForm == 'going' \
            and self.preHeadForm in forms.be

    def nodeIsPastUsedTo(self):
        return len(self.trueChunk) == 1 \
            and self.headForm == 'used' \
            and self.headPos == 'VBD'

    def nodeIsDoAuxiliar(self):
        return self.headForm in forms.do
       
    def normalizeMod(self, form):
        if form == 'ca': return 'can'
        elif form == "'d": return 'would'
        else: raise "ERROR: unknown modal form: "+str(form)

    def normalizeHave(self, form):
        if form == "'d": return 'had'
        elif form == "'s": return 'has'
        elif form == "'ve": return 'have'
        else: raise "ERROR: unknown raise form: "+str(form)

    def getPolarity(self):
        if self.negative:
            for item in self.adverbsPre:
                # verbal chunks containing 'not only' have positive polarity
                if item.getText() == 'only':
                    return "POS"
        return "NEG" if self.negative else "POS"

    def getEventClass(self):
        """Return the event class for the nominal, using the regeluar expressions
        in the library."""
        try:
            head = self.head.getText()
        except AttributeError:
            # This is used when the head is None, which can be the case for some
            # weird (and incorrect) chunks, like [to/TO] (MV 11//08/07)
            logger.warn("Cannot assign class to incorrect chunk")
            return None
        head = 'is' if head in forms.be else DictVerbStems.get(head, head.lower())
        try:
            if forms.istateprog.match(head): return  'I_STATE'
            elif forms.reportprog.match(head): return 'REPORTING'
            elif forms.percepprog.match(head): return 'PERCEPTION'
            elif forms.iactionprog.match(head): return 'I_ACTION'
            elif forms.aspect1prog.match(head): return 'ASPECTUAL'
            elif forms.aspect2prog.match(head): return 'ASPECTUAL'
            elif forms.aspect3prog.match(head): return 'ASPECTUAL'
            elif forms.aspect4prog.match(head): return 'ASPECTUAL'
            elif forms.aspect5prog.match(head): return 'ASPECTUAL'
            elif forms.stateprog.match(head): return 'STATE'
            else: return 'OCCURRENCE'
        except:
            logger.warn("Error running event class patterns")

    def as_verbose_string(self):
        if self.node is None:
            opening_string = 'GramVChunk: None'
        else:
            opening_string = "GramVChunk: %s" % self.node.getText()
        try:
            head_string = self.head.getText()
        except AttributeError:
            head_string = ''
        return \
            opening_string + "\n" + \
            "\tTENSE=%s ASPECT=%s HEAD=%s CLASS=%s\n" \
            % (self.tense, self.aspect, self.head.getText(), self.evClass) + \
            "\tNF_MORPH=%s MODALITY=%s POLARITY=%s\n" \
            % (self.nf_morph, self.modality, self.polarity) + \
            "\tNEGATIVE:" + str(getWordList(self.negative)) + "\n" + \
            "\tINFINITIVE:" + str(getWordList(self.infinitive)) + "\n" + \
            "\tADVERBS-pre:" + str(getWordList(self.adverbsPre)) + "\n" + \
            "\tADVERBS-post:%s%s\n" % (getWordList(self.adverbsPost), getPOSList(self.adverbsPost)) + \
            "\tTRUE CHUNK:%s%s\n" % (getWordList(self.trueChunk), getPOSList(self.trueChunk))

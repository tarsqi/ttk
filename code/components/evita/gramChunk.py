"""

This module contains classes that add grammatical features to NounChunks,
VerbChunks and AdjectiveTokens. The grammatical features drive part of the event
recognition.

"""

# TODO. Some old functionality that seemed better suited for NounChunk was
# removed, but there may still be functionality on GramVChunk that should really
# be on VerbChunk.


from types import ListType, InstanceType
from pprint import pprint

import utilities.porterstemmer as porterstemmer
import utilities.logger as logger
from utilities.file import open_pickle_file

from library import forms
from library.evita.patterns.feature_rules import FEATURE_RULES

from components.common_modules.utils import get_tokens, remove_interjections
from components.common_modules.utils import contains_adverbs_only
from components.evita.rule import FeatureRule

DEBUG = True
DEBUG = False


# open the pickle file with verbstem information
DictVerbStems = open_pickle_file(forms.DictVerbStemPickleFileName)

# initialize a stemmer
stemmer = porterstemmer.Stemmer()


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

def debug(text, newline=True):
    if DEBUG:
        if newline: print text
        else: print text,


class GramChunk:

    """The subclasses of this class are used to add grammatical features to a

    NounChunk, VerbChunk or AdjectiveToken. It lives in the gramchunk variable
    of instances of those classes."""

    def __init__(self, chunk_or_token, gramvchunk):
        """Common initialization for GramNChunk and GramAChunk."""
        self.node = chunk_or_token
        self.tense = "NONE"
        self.aspect = "NONE"
        self.modality = "NONE"
        self.polarity = "POS"
        self.add_verb_features(gramvchunk)

    def add_verb_features(self, gramvchunk):
        """Set some features (tense, aspect, modality and polarity) to the values of
        those features on the governing verb."""
        if gramvchunk is not None:
            self.tense = gramvchunk.tense
            self.aspect = gramvchunk.aspect
            self.modality = gramvchunk.modality
            self.polarity = gramvchunk.polarity

    def print_vars(self):
        pprint(vars(self))

    def as_verbose_string(self):
        """Debugging method to print the GramChunk and its features."""
        return \
            "%s: %s\n" % (self.__class__.__name__, self.node.getText()) + \
            "\ttense=%s aspect=%s head=%s class=%s\n" \
            % (self.tense, self.aspect, self.head.getText(), self.evClass) + \
            "\tnf_morph=%s modality=%s polarity=%s\n" \
            % (self.nf_morph, self.modality, self.polarity)


class GramAChunk(GramChunk):

    """Contains the grammatical features for an AdjectiveToken."""

    def __init__(self, adjectivetoken, gramvchunk=None):
        """Initialize with an AdjectiveToken and use default values for most instance
        variables, but percolate grammatical features from the copular verb if
        they were handed in."""
        GramChunk.__init__(self, adjectivetoken, gramvchunk)
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

    def __init__(self, nounchunk, gramvchunk=None):
        """Initialize with a NounChunk and use default values for most instance
        variables."""
        GramChunk.__init__(self, nounchunk, gramvchunk)
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


class GramVChunkList:

    """This class is used to create a list of GramVChunk instances. What it does
    is (1) collecting information form a VerbChunk or a list of Tokens, (2) move
    this information into separate bins depending on the type of items in the
    source, (3) decide whether we need more than one GramVChunk for some input,
    and (4) create a list of VerbChunks.

    Where a GramNChunk is given a NounChunk on initialization, a GramVChunkList
    is given a VerbChunk or a list of Tokens (or maybe other categories as well)
    GramVChunks are different from NounChunks in that there can be more than one
    GramVChunk for a VerbChunk. This is not very common, but it happens for
    example in

       "More problems in Hong Kong for a place, for an economy, that many
        experts [thought was] once invincible."

    where "thought was" ends up as one verb chunk.

    Another difference is that sometimes a GramVChunk is created for tokens
    including tokens to the right of the VerbChunk, for example in

       "All Arabs [would have] [to move] behind Iraq."

    where there are two adjacent VerbChunks. With the current implementation,
    when processing [would have], we end up creating GramVChunks for "would
    have" and "would have to move", and then, when dealing with [to move", we
    create a GramVChunk for "to move".

    TODO: check whether "would have" and "to move" should be ruled out
    TODO: check why "to move" is not already ruled out through the flag

    Note that in both cases, the root of the issue is that the chunking is not
    appropriate for Evita.

    TODO: consider updating the Chunker and simplifying the code here.

    """

    def __init__(self, verbchunk=None, tokens=None):
        """Initialize several kinds of lists, distributing information from the
        VerbChunk or list of Tokens that is handed in on initialization and
        create a list of GramVChunks in self.gramVChunksList."""
        source = "VerbChunk" if verbchunk else "Tokens"
        logger.debug("Initializing GramVChunkList from %s" % source)
        self._initialize_nodes(verbchunk, tokens)
        self._initialize_lists()
        self._distributeNodes()
        self._generateGramVChunks()

    def _initialize_nodes(self, verbchunk, tokens):
        """Given the VerbChunk or a list of Tokens, set the nodes variable to
        either the daughters of the VerbChunk or the list of Tokens. Also sets
        node and tokens, where the first one has the VerbChunk or None (this is
        so we can hand the chunk to GramVChunk, following GramChunk behaviour),
        and where the second one is the list of Tokens or None."""
        if verbchunk:
            self.node = verbchunk
            self.tokens = None
            self.nodes = verbchunk.dtrs
        elif tokens:
            self.node = None
            self.tokens = tokens
            self.nodes = tokens
        else:
            logger.error("Incorrect initialization of GramVChunkList")

    def _initialize_lists(self):
        """Initializes the lists that contain items (Tokens) of the chunk. Since
        one chunk may spawn more than one GramVChunk, these lists are actually
        lists of lists."""
        self.counter = 0            # controls different subchunks in a chunk
        self.gramVChunksList = []   # this is the list of GramVChunk instances
        self.trueChunkLists = [[]]  # the core of the chunk
        self.negMarksLists = [[]]
        self.infMarkLists = [[]]
        self.adverbsPreLists = [[]]
        self.adverbsPostLists = [[]]
        self.leftLists = [[]]
        self.chunkLists = [self.trueChunkLists, self.negMarksLists, self.infMarkLists,
                           self.adverbsPreLists, self.adverbsPostLists, self.leftLists]

    def __len__(self):
        return len(self.gramVChunksList)

    def __getitem__(self, index):
        return self.gramVChunksList[index]

    def __str__(self):
        if len(self.gramVChunksList) == 0:
            return '[]'
        string = ''
        for i in self.gramVChunksList:
            node = "\n\tNEGATIVE: " + str(getWordList(i.negative)) \
                + "\n\tINFINITIVE: "  + str(getWordList(i.infinitive)) \
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

    def is_wellformed(self):
        """Return True if this GramVChunkList is well-formed, that is, it has content
        and at least one true chunk."""
        true_chunks = self.trueChunkLists
        if len(true_chunks) == 1 and not true_chunks[0]:
            return False
        if len(self) == 0:
            logger.warn("Empty GramVChList")
            return False
        return True

    def _distributeNodes(self):
        """Distribute the item information over the lists in the GramVChunkLists."""
        # TODO: figure out whether to keep remove_interjections
        tempNodes = remove_interjections(self)
        debug("\n" + '-'.join([n.getText() for n in tempNodes]))
        logger.debug('-'.join([n.getText() for n in tempNodes]))
        itemCounter = 0
        for item in tempNodes:
            debug( "   %s  %-3s  %-8s" % (itemCounter, item.pos, item.getText()), newline=False)
            if item.pos == 'TO':
                self._distributeNode_TO(item, itemCounter)
            elif item.getText() in forms.negative:
                self._distributeNode_NEG(item)
            elif item.pos == 'MD':
                self._distributeNode_MD(item)
            elif item.pos[0] == 'V':
                self._distributeNode_V(item, tempNodes, itemCounter)
            elif item.pos in forms.partAdv:
                self._distributeNode_ADV(item, tempNodes, itemCounter)
            else:
                debug( '==> None')
            itemCounter += 1
            if DEBUG:
                self.print_trueChunkLists()

    def _distributeNode_TO(self, item, itemCounter):
        """If the item is the first one, just add the item to the infinitive markers
        list. Otherwise, see if the last element in the core is one of a small
        group ('going', 'used' and forms of 'have'), if it is, add the element to the
        core, if not, do nothing at all."""
        debug( '==> TO')
        if itemCounter == 0:
            self._addInCurrentSublist(self.infMarkLists, item)
        else:
            # This case should only occur if a chunk was extended with a method
            # on VerbChunk (_createEventOnHave, _createEventOnFutureGoingTo and
            # _createEventOnPastUsedTo).
            try:
                if self.trueChunkLists[-1][-1].getText() \
                   in ['going', 'used', 'has', 'had', 'have', 'having']:
                    self._addInCurrentSublist(self.trueChunkLists, item)
                else:
                    # Given the VerbChunk methods used above, this should
                    # probably never happen.
                    logger.warn("Unexpected input for GramVChunkList")
            except IndexError:
                logger.warn("Unexpected input for GramVChunkList")

    def _distributeNode_NEG(self, item):
        """Do not add the negation item to the core in self.trueChunkLists, but add it
        to the list with negation markers."""
        debug( '==> NEG')
        self._addInCurrentSublist(self.negMarksLists, item)

    def _distributeNode_MD(self, item):
        """Add the modifier element to the core list."""
        debug( '==> MD')
        self._addInCurrentSublist(self.trueChunkLists, item)

    def _distributeNode_V(self, item, tempNodes, itemCounter):
        debug( '==> V')
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
                    self._addInCurrentSublist(self.trueChunkLists, item)
                else:
                    self._treatMainVerb(item, tempNodes, itemCounter)
            except:
                self._treatMainVerb(item, tempNodes, itemCounter)
        else:
            self._addInCurrentSublist(self.trueChunkLists, item)

    def _distributeNode_ADV(self, item, tempNodes, itemCounter):
        debug( '==> ADV')
        if item != tempNodes[-1]:
            if len(tempNodes) > itemCounter+1:
                if (tempNodes[itemCounter+1].pos == 'TO' or
                    contains_adverbs_only(tempNodes[itemCounter:])):
                    self._addInPreviousSublist(self.adverbsPostLists, item)
                else:
                    self._addInCurrentSublist(self.adverbsPreLists, item)
            else:
                self._addInCurrentSublist(self.adverbsPostLists, item)
        else:
            self._addInPreviousSublist(self.adverbsPostLists, item)

    def print_trueChunkLists(self):
        for trueChunkList in self.trueChunkLists:
            print "   tc [%s]" % (', '.join(["%s" % x.text for x in trueChunkList]))

    def _treatMainVerb(self, item, tempNodes, itemCounter):
        self._addInCurrentSublist(self.trueChunkLists, item)
        # TODO: it is weird that the counter is updated independently from
        # updating the chunk lists, fin dout why
        self._updateCounter()
        if (item == tempNodes[-1] or
            contains_adverbs_only(tempNodes[itemCounter+1:])):
            pass
        else:
            self._updateChunkLists()

    def _updateCounter(self):
        self.counter += 1

    def _updateChunkLists(self):
        """Append an empty list to the end of all lists maintained in the
        GramVChunkList. Necessary for dealing with chunks containing subchunks,
        for example '[[might consider] [filing]]'."""
        for chunkList in self.chunkLists:
            # TODO: why do we have this test?
            if len(chunkList) == self.counter:
                chunkList.append([])
            else:
                logger.warn("length of chunk list and counter are out of sync")

    def _addInCurrentSublist(self, sublist, element):
        """Add the element to the current element (that is, the last element) in
        sublist. The elements of the sublist are lists themselves."""
        if len(sublist) - self.counter == 1:
            sublist[self.counter].append(element)
        else:
            logger.warn("length of chunk list and counter are out of sync")

    def _addInPreviousSublist(self, sublist, element):
        """Add the element to the previous element (that is, the penultimate
        element) in sublist. The elements of the sublist are lists themselves."""
        # TODO: this is used only once in all of the tests evita-BE.xml, look
        # into what this case is; also, the logic of how this works and the
        # interaction with self.counter is a bit unclear, it can probably be
        # simplified
        if len(sublist) >= self.counter-1:
            sublist[self.counter-1].append(element)
        else:
            logger.warn("list should be longer")
        #print '>>>', len(sublist), self.counter
        #print sublist

    def _generateGramVChunks(self):
        for idx in range(len(self.trueChunkLists)):
            gramVCh = GramVChunk(self.node,
                                 self.trueChunkLists[idx],
                                 self.negMarksLists[idx],
                                 self.infMarkLists[idx],
                                 self.adverbsPreLists[idx],
                                 self.adverbsPostLists[idx],
                                 self.leftLists[idx])
            self.gramVChunksList.append(gramVCh)


class GramVChunk(GramChunk):

    def __init__(self, verbchunk, tCh, negMk, infMk, advPre, advPost, left):
        # TODO: note that there is not a straight correspondence between the
        # VerbChunk and the tokens that the GramVChunk is for, how do we know
        # that the right event is added?
        self.node = verbchunk
        self.trueChunk = tCh
        self.negative = negMk
        self.infinitive = infMk            # does not appear to be used
        self.adverbsPre = advPre
        self.adverbsPost = advPost
        self.left = left
        self.head = self.getHead()
        self.evClass = self.getEventClass()
        self.tense = 'NONE'
        self.aspect = 'NONE'
        self.nf_morph = 'VERB'
        self.set_tense_and_aspect()
        self.modality = self.getModality()
        self.polarity = self.getPolarity()
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
            logger.warn("empty trueChunk, head is set to None")
            return None

    def getPreHead(self):
        if self.trueChunk and len(self.trueChunk) > 1:
            return  self.trueChunk[-2]
        else:
            return None

    def set_tense_and_aspect(self):
        """Sets the tense and aspect attributes by overwriting the default
        values with results from the feature rules in FEATURE_RULES. If no
        feature rules applied, create a throw-away GramVChunk for the head and
        use the features from there (which might still be defaults)."""
        features = self.apply_feature_rules()
        if features is not None:
            (tense, aspect, nf_morph) = features
            self.tense = tense
            self.aspect = aspect
        elif len(self.trueChunk) > 1 and self.head is not None:
            gramvchunk = GramVChunkList(tokens=[self.head])[0]
            self.tense = gramvchunk.tense
            self.aspect = gramvchunk.aspect

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

    def nodeIsModal(self, nextNode):
        return self.headPos == 'MD' and nextNode

    def nodeIsBe(self, nextNode):
        return self.headForm in forms.be and nextNode

    def nodeIsBecome(self, nextNode):
        return self.headForm in forms.become and nextNode

    def nodeIsContinue(self, nextNode):
        return forms.RE_continue.match(self.headForm) and nextNode

    def nodeIsKeep(self, nextNode):
        return forms.RE_keep.match(self.headForm) and nextNode

    def nodeIsHave(self):
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
            text = self.head.getText()
        except AttributeError:
            # This is used when the head is None, which can be the case for some
            # weird (and incorrect) chunks, like [to/TO] (MV 11//08/07)
            logger.warn("Cannot assign class to incorrect chunk")
            return None
        stem = 'is' if text in forms.be else DictVerbStems.get(text, text.lower())
        try:
            if forms.istateprog.match(stem): return  'I_STATE'
            elif forms.reportprog.match(stem): return 'REPORTING'
            elif forms.percepprog.match(stem): return 'PERCEPTION'
            elif forms.iactionprog.match(stem): return 'I_ACTION'
            elif forms.aspect1prog.match(stem): return 'ASPECTUAL'
            elif forms.aspect2prog.match(stem): return 'ASPECTUAL'
            elif forms.aspect3prog.match(stem): return 'ASPECTUAL'
            elif forms.aspect4prog.match(stem): return 'ASPECTUAL'
            elif forms.aspect5prog.match(stem): return 'ASPECTUAL'
            elif forms.stateprog.match(stem): return 'STATE'
            else: return 'OCCURRENCE'
        except:
            logger.warn("Error running event class patterns")

    def as_verbose_string(self):
        if self.node is None:
            opening_string = 'GramVChunk: None'
        else:
            # TODO: this crashes since often self.node is a list
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

"""

This module contains classes that add grammatical features to NounChunks,
VerbChunks and AdjectiveTokens. The grammatical features drive part of the event
recognition.

"""

# TODO: check whether these are used by Slinket, if so move it to common_modules


from types import ListType, InstanceType
from pprint import pprint

import utilities.stemmer as stemmer
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
stemmer = stemmer.Stemmer()


def getWordList(constituents):
    """Returns a list of words from the list of constituents, typically the
    constituents are instances of NounChunk, VerbChunk or Token. Used for
    debugging purposes."""
    return [str(constituent.getText()) for constituent in constituents]

def getPOSList(constituents):
    """Returns a list of parts-of-speech from the list of constituents, typically
    the constituents are instances of NounChunk, VerbChunk or Token. Used for
    debugging purposes."""
    return [constituent.pos for constituent in constituents]

def getWordPosList(constituents):
    """Returns a list of word/POS for all constituents."""
    return ["%s/%s" % (s, t) for s, t
            in zip(getWordList(constituents), getPOSList(constituents))]

def debug(text, newline=True):
    if DEBUG:
        if newline: print text
        else: print text,


class ChunkFeatures:

    """The subclasses of this class are used to add grammatical features to a
    NounChunk, VerbChunk or AdjectiveToken. It lives in the features variable
    of instances of those classes."""

    def __init__(self, category, chunk_or_token, verbfeatures=None):
        """Common initialization for AChunkFeatures, NChunkFeatures and
        VChunkFeatures."""
        self.nf_morph = category
        self.node = chunk_or_token
        self.head = None
        self.evClass = None
        self.tense = "NONE"
        self.aspect = "NONE"
        self.modality = "NONE"
        self.polarity = "POS"
        self.add_verb_features(verbfeatures)

    def __str__(self):
        return "<NChunkFeatures %s %s %s %s %s %s %s>" \
            % (self.nf_morph, self.evClass, self.tense, self.aspect,
               self.modality, self.polarity, self.head)

    def add_verb_features(self, verbfeatures):
        """Set some features (tense, aspect, modality and polarity) to the values of
        those features on the governing verb."""
        if verbfeatures is not None:
            self.tense = verbfeatures.tense
            self.aspect = verbfeatures.aspect
            self.modality = verbfeatures.modality
            self.polarity = verbfeatures.polarity

    def print_vars(self):
        """Debugging method to print all variables."""
        pprint(vars(self))

    def as_verbose_string(self):
        """Debugging method to print the ChunkFeatures and its features."""
        return \
            "%s: %s\n" % (self.__class__.__name__, self.node.getText()) + \
            "\ttense=%s aspect=%s head=%s class=%s\n" \
            % (self.tense, self.aspect, self.head.getText(), self.evClass) + \
            "\tnf_morph=%s modality=%s polarity=%s\n" \
            % (self.nf_morph, self.modality, self.polarity)


class AChunkFeatures(ChunkFeatures):

    """Contains the grammatical features for an AdjectiveToken. There is a
    little naming disconnect here since we call these chunk features."""

    def __init__(self, adjectivetoken, verbfeatures=None):
        """Initialize with an AdjectiveToken and use default values for most instance
        variables, but percolate grammatical features from the copular verb if
        they were handed in."""
        ChunkFeatures.__init__(self, "ADJECTIVE", adjectivetoken, verbfeatures)
        self.head = adjectivetoken
        self.evClass = self.getEventClass()

    def getEventClass(self):
        """Return I_STATE if the head is on a short list of intentional state
        adjectives, return STATE otherwise."""
        headString = self.head.getText()
        return 'I_STATE' if headString in forms.istateAdj else 'STATE'


class NChunkFeatures(ChunkFeatures):

    """Contains the grammatical features for a NounChunk."""

    def __init__(self, nounchunk, verbfeatures=None):
        """Initialize with a NounChunk and use default values for most instance
        variables."""
        ChunkFeatures.__init__(self, "NOUN", nounchunk, verbfeatures)
        self.head = self.node.getHead()
        self.evClass = self.getEventClass()
        self.head_lemma = self.getEventLemma()

    def getEventClass(self):
        """Get the event class for the ChunkFeatures. For nominals, the event
        class is always OCCURRENCE."""
        return "OCCURRENCE"
  
    def getEventLemma(self):
        """Return the lemma from the head of the chunk. If there is no head or
        the head has no lemma, then build it from the text using a stemmer."""
        try:
            return self.head.lemma
        except AttributeError:
            return stemmer.stem(self.head.getText().lower())


class VChunkFeatures(ChunkFeatures):

    """Contains the grammatical features for a VerbChunk. Applies some feature
    rules from the evita library in the course of setting tense and aspect
    features. Also has some methods that test whether the features indicate
    whether the node is of a particular kind (for example, nodeIsbecome)."""

    def __init__(self, verbchunk, tCh, negMk, infMk, advPre, advPost):
        """Initialize with a verb chunk and the lists handed in from the
        VChunkFeaturesList object."""
        # TODO: note that there is not a straight correspondence between the
        # VerbChunk and the tokens that the VChunkFeatures instance is for,
        # so how do we know that the right event is added?
        ChunkFeatures.__init__(self, "VERB", verbchunk)
        self.trueChunk = tCh
        self.head = self.getHead()          # this depends on self.trueChunk
        self.evClass = self.getEventClass() # this depends on self.head
        self.negative = negMk
        self.infinitive = infMk             # does not appear to be used
        self.adverbsPre = advPre
        self.adverbsPost = advPost
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
            "<VChunkFeatures %s %s %s trueChunk=[%s]>" \
            % (self.evClass, self.tense, self.aspect,
               ', '.join(getWordPosList(self.trueChunk)))

    def is_wellformed(self):
        """Return True if the verb features well-formed, that is, there is
        content in the trueChunks core feature and there is a head."""
        return self.trueChunk and self.head

    def isAuxVerb(self):
        """Return True if the head is an auxiliary verb."""
        return True if self.head.getText().lower() in forms.auxVerbs else False

    def getHead(self):
        """Return the head, which is the last element of the core in
        self.trueChunk, return None if there is no such core."""
        if self.trueChunk:
            return self.trueChunk[-1]
        else:
            logger.warn("empty trueChunk, head is set to None")
            return None

    def getPreHead(self):
        """Return the element before the head, which is the last element of the
        core in self.trueChunk, return None if there is no such element."""
        if self.trueChunk and len(self.trueChunk) > 1:
            return  self.trueChunk[-2]
        else:
            return None

    def set_tense_and_aspect(self):
        """Sets the tense and aspect attributes by overwriting the default
        values with results from the feature rules in FEATURE_RULES. If no
        feature rules applied, create a throw-away features list for the head
        and use the features from there (which might still be defaults)."""
        features = self.apply_feature_rules()
        if features is not None:
            (tense, aspect, nf_morph) = features
            self.tense = tense
            self.aspect = aspect
        elif len(self.trueChunk) > 1 and self.head is not None:
            features = VChunkFeaturesList(tokens=[self.head])[0]
            self.tense = features.tense
            self.aspect = features.aspect

    def apply_feature_rules(self):
        """Returns a triple of TENSE, ASPECT and CATEGORY given the tokens of
        the chunk, which are stored in self.trueChunk. Selects the rules
        relevant for the length of the chunk and applies them. Returns None if
        no rule applies."""
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

    def is_modal(self):
        return self.headPos == 'MD'

    def is_be(self):
        return self.headForm in forms.be

    def is_become(self):
        return self.headForm in forms.become

    def is_continue(self):
        return forms.RE_continue.match(self.headForm)

    def is_keep(self):
        return forms.RE_keep.match(self.headForm)

    def is_have(self):
        return self.headForm in forms.have and self.headPos is not 'MD'

    def is_future_going_to(self):
        return len(self.trueChunk) > 1 \
            and self.headForm == 'going' \
            and self.preHeadForm in forms.be

    def is_past_used_to(self):
        return len(self.trueChunk) == 1 \
            and self.headForm == 'used' \
            and self.headPos == 'VBD'

    def is_do_auxiliar(self):
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
        """Return the event class for the nominal, using the regelar expressions
        in the library."""
        try:
            text = self.head.getText()
        except AttributeError:
            # This is used when the head is None, which can be the case for some
            # weird (and incorrect) chunks, like [to/TO]
            # TODO: make sure this cannot happen
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

    def as_short_string(self):
        return "<VChunkFeatures trueChunk=[%s]>" \
            % ', '.join(getWordPosList(self.trueChunk))

    def as_verbose_string(self):
        if self.node is None:
            opening_string = 'VChunkFeatures: None'
        else:
            # TODO: this crashes since often self.node is a list
            opening_string = "VChunkFeatures: '%s'" % self.node.getText().strip()
        try:
            head_string = self.head.getText().strip()
        except AttributeError:
            head_string = ''
        return \
            opening_string + "\n" \
            + "\ttense=%s aspect=%s head=%s class=%s\n" \
            % (self.tense, self.aspect, self.head.getText(), self.evClass) \
            + "\tnf_morph=%s modality=%s polarity=%s\n" \
            % (self.nf_morph, self.modality.replace(' ', '-'), self.polarity) \
            + "\ttrueChunk: [%s]\n" % ', '.join(getWordPosList(self.trueChunk)) \
            + "\tnegative:  [%s]\n"  % ', '.join(getWordPosList(self.negative)) \
            + "\tinfinitive: [%s]\n"  % ', '.join(getWordPosList(self.infinitive)) \
            + "\tadverbs-pre: [%s]\n" % ', '.join(getWordPosList(self.adverbsPre)) \
            + "\tadverbs-post: [%s]\n" %  ', '.join(getWordPosList(self.adverbsPost))

    def pp(self, verbose=False):
        if verbose:
            print self.as_verbose_string()
        else:
            print self


class VChunkFeaturesList:

    """This class is used to create a list of VChunkFeatures instances. What
    it does is (1) collecting information from a VerbChunk or a list of Tokens,
    (2) move this information into separate bins depending on the type of items
    in the source, (3) decide whether we need more than one instance for some
    input, and (4) create a list of VChunkFeatures.

    On initialization, an instance of NChunkFeatures is given a NounChunk, but a
    VChunkFeaturesList is given a VerbChunk or a list of Tokens (or maybe
    other categories as well). VerbChunks are different from NounChunks in that
    there can be more than one VChunkFeatures instance for a single
    VerbChunk. This is not very common, but it happens for example in

       "More problems in Hong Kong for a place, for an economy, that many
        experts [thought was] once invincible."

    where "thought was" ends up as one verb chunk, but we get two features sets.

    Another difference is that sometimes a VChunkFeatures instance is created
    for a sequence that includes tokens to the right of the VerbChunk, for
    example in

       "All Arabs [would have] [to move] behind Iraq."

    where there are two adjacent VerbChunks. With the current implementation,
    when processing [would have], we end up creating VChunkFeatures instances
    for "would have" and "would have to move", and then, when dealing with "to
    move", we create a VChunkFeatures instance for "to move".

    TODO: check whether "would have" and "to move" should be ruled out
    TODO: check why "to move" is not already ruled out through the flag

    Note that in both cases, the root of the issue is that the chunking is not
    appropriate for Evita.

    TODO: consider updating the Chunker and simplifying the code here.

    """

    def __init__(self, verbchunk=None, tokens=None):
        """Initialize several kinds of lists, distributing information from the
        VerbChunk or list of Tokens that is handed in on initialization and
        create a list of VChunkFeatures instances in self.featuresList."""
        source = "VerbChunk" if verbchunk else "Tokens"
        logger.debug("Initializing VChunkFeaturesList from %s" % source)
        self.node = verbchunk
        self.tokens = tokens
        self._initialize_nodes()
        self._initialize_lists()
        self._distributeNodes()
        self._generate_features_list()
        if DEBUG: print "\n", self

    def _initialize_nodes(self):
        """Given the VerbChunk or a list of Tokens, set the nodes variable to
        either the daughters of the VerbChunk or the list of Tokens. Also sets
        node and tokens, where the first one has the VerbChunk or None (this is
        so we can hand the chunk to VChunkFeatures instance, following
        ChunkFeatures behaviour), and where the second one is the list of Tokens
        or None."""
        if self.node:
            self.nodes = self.node.dtrs
        elif self.tokens:
            self.nodes = self.tokens
        else:
            logger.error("Incorrect initialization of VChunkFeaturesList")

    def _initialize_lists(self):
        """Initializes the lists that contain items (Tokens) of the chunk. Since
        one chunk may spawn more than one VChunkFeatures instance, these
        lists are actually lists of lists."""
        self.featuresList = []      # the list of VChunkFeatures instances
        self.counter = 0            # controls different subchunks in a chunk
        self.trueChunkLists = [[]]  # the cores of the subchunks
        self.negMarksLists = [[]]
        self.infMarkLists = [[]]
        self.adverbsPreLists = [[]]
        self.adverbsPostLists = [[]]
        self.chunkLists = [self.trueChunkLists, self.negMarksLists, self.infMarkLists,
                           self.adverbsPreLists, self.adverbsPostLists]

    def __len__(self):
        return len(self.featuresList)

    def __getitem__(self, index):
        return self.featuresList[index]

    def __str__(self):
        words = '-'.join(getWordList(self.nodes))
        return \
            "<VChunkFeaturesList length=%d words=%s>\n\n" % (len(self), words) + \
            "\n".join([gvch.as_verbose_string() for gvch in self.featuresList])

    def _distributeNodes(self):
        """Distribute the item's information over the lists in the
        VChunkFeaturesLists."""
        # TODO: figure out whether to keep remove_interjections
        tempNodes = remove_interjections(self)
        debug("\n" + '-'.join([n.getText() for n in tempNodes]))
        logger.debug('-'.join([n.getText() for n in tempNodes]))
        itemCounter = 0
        for item in tempNodes:
            #debug( "   %s  %-3s  %-8s"
            #       % (itemCounter, item.pos, item.getText()), newline=False)
            message_prefix = "   %s  %s/%s" % (itemCounter, item.getText(), item.pos)
            if item.pos == 'TO':
                debug( '%s  ==>  TO' % message_prefix)
                self._distributeNode_TO(item, itemCounter)
            elif item.getText() in forms.negative:
                debug( '%s  ==>  NEG' % message_prefix)
                self._distributeNode_NEG(item)
            elif item.pos == 'MD':
                debug( '%s  ==>  MD' % message_prefix)
                self._distributeNode_MD(item)
            elif item.pos[0] == 'V':
                debug( '%s  ==>  V' % message_prefix)
                self._distributeNode_V(item, tempNodes, itemCounter)
            elif item.pos in forms.partAdv:
                debug( '%s  ==>  ADV' % message_prefix)
                self._distributeNode_ADV(item, tempNodes, itemCounter)
            else:
                debug( '%s  ==>  None' % message_prefix)
            itemCounter += 1
            if DEBUG:
                self.print_ChunkLists()

    def _distributeNode_TO(self, item, itemCounter):
        """If the item is the first one, just add the item to the infinitive markers
        list. Otherwise, see if the last element in the core is one of a small
        group ('going', 'used' and forms of 'have'), if it is, add the element to the
        core, if not, do nothing at all."""
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
                    logger.warn("Unexpected input for VChunkFeaturesList")
            except IndexError:
                logger.warn("Unexpected input for VChunkFeaturesList")

    def _distributeNode_NEG(self, item):
        """Do not add the negation item to the core in self.trueChunkLists, but add it
        to the list with negation markers."""
        self._addInCurrentSublist(self.negMarksLists, item)

    def _distributeNode_MD(self, item):
        """Add the modal element to the core list."""
        self._addInCurrentSublist(self.trueChunkLists, item)

    def _distributeNode_V(self, item, tempNodes, itemCounter):
        """Add a verb to the lists. This takes one of two actions, depending on the kind
        of verb we are dealing with and on whether it is followed by TO."""
        if item == tempNodes[-1]:
            # if the verb is the last item, it can simply be added to the core.
            self._addInCurrentSublist(self.trueChunkLists, item)
        elif item.isMainVerb():
            if item.getText() in ['going', 'used', 'had', 'has', 'have', 'having']:
                # this makes sure that verbs like "going" in "going to sleep"
                # are not treated as regular main verbs (for regular main verbs
                # we would create two subchunks
                if self._item_is_followed_by_TO(tempNodes, itemCounter):
                    self._addInCurrentSublist(self.trueChunkLists, item)
                else:
                    self._treatMainVerb(item, tempNodes, itemCounter)
            else:
                self._treatMainVerb(item, tempNodes, itemCounter)
        else:
            self._addInCurrentSublist(self.trueChunkLists, item)

    def _distributeNode_ADV(self, item, tempNodes, itemCounter):
        """Just add the adverb to an adverb list, the trick is to figure out which list
        to add it. Factors are the location of the item in the tempNodes list
        and the pos tags of the elements following the item."""
        # TODO. This does often not do the right thing. For example, in the
        # phrase 'will end up being eliminated', we get two VChunkFeatures
        # instances, but 'up' will live in the adverbsPre list of the second one
        # (instead of in the adverbsPost list of the first). This is of limited
        # negative effect since the only thing that the adverbs are used for is
        # to scan the adverbPre list for 'only', which has effect on the
        # polarity.
        if item != tempNodes[-1]:
            debug("      NOT LAST")
            if len(tempNodes) > itemCounter+1:
                debug('        tempNodes IS LONG')
                if (tempNodes[itemCounter+1].pos == 'TO' or
                    contains_adverbs_only(tempNodes[itemCounter:])):
                    # this would apply to text like "end up in Tokyo" but the
                    # chunker does not recognize "end up" as a <vg>
                    debug('          NEXT IS TO OR REST IS ADVERBS')
                    self._addInPreviousSublist(self.adverbsPostLists, item)
                else:
                    debug('          NEXT IS NOT TO AND REST IS NOT ADVERBS')
                    self._addInCurrentSublist(self.adverbsPreLists, item)
            else:
                debug('        tempNodes IS NOT LONG')
                self._addInCurrentSublist(self.adverbsPostLists, item)
        else:
            debug("      LAST")
            self._addInPreviousSublist(self.adverbsPostLists, item)

    def _item_is_followed_by_TO(self, tempNodes, itemCounter):
        """Return True if one of the next two tokens is TO, return False otherwise."""
        try:
            return (tempNodes[itemCounter+1].getText() == 'to' or
                    tempNodes[itemCounter+2].getText() == 'to')
        except IndexError:
            return False

    def _treatMainVerb(self, item, tempNodes, itemCounter):
        """Add a main verb to the trueChunks list. That is all that is done when the
        item is followed by adverbs only. In other cases, we have a chunk which
        has two subchunks and _updateChunkLists is called to introduce the
        second chunk. This is to deal with cases like 'might consider filing',
        where we want to end up with two events."""
        self._addInCurrentSublist(self.trueChunkLists, item)
        if not contains_adverbs_only(tempNodes[itemCounter+1:]):
            self._updateChunkLists()

    def _updateChunkLists(self):
        """Append an empty list to the end of all lists maintained in the
        VChunkFeaturesList and update the counter."""
        self.counter += 1
        for chunkList in self.chunkLists:
            chunkList.append([])

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
        # TODO. This method is never used in the 300+ sentences in the tests in
        # testing/scripts/regression/evita/data-in. There is a use case for this
        # method though with phrases like "end up being eliminated", where "up"
        # should be added to the previous and not current list, which is now not
        # dealt with properly. Also, the logic of this method is a bit odd in
        # that when the counter is 0 the item will be added to the last (and
        # current) list, maybe want a warning instead.
        if len(sublist) >= self.counter-1:
            sublist[self.counter-1].append(element)
        else:
            # not sure whether this can actually occur
            logger.warn("list should be longer")

    def _generate_features_list(self):
        for idx in range(len(self.trueChunkLists)):
            features = VChunkFeatures(
                self.node, self.trueChunkLists[idx],
                self.negMarksLists[idx], self.infMarkLists[idx],
                self.adverbsPreLists[idx], self.adverbsPostLists[idx])
            self.featuresList.append(features)

    def print_ChunkLists(self):
        for i in range(len(self.trueChunkLists)):
            sep = ', '
            tc =  sep.join(["%s" % x.text for x in self.trueChunkLists[i]])
            neg =  sep.join(["%s" % x.text for x in self.negMarksLists[i]])
            inf =  sep.join(["%s" % x.text for x in self.infMarkLists[i]])
            adv1 =  sep.join(["%s" % x.text for x in self.adverbsPreLists[i]])
            adv2 =  sep.join(["%s" % x.text for x in self.adverbsPostLists[i]])
            print "      tc=[%s] inf=[%s] neg=[%s] adv1=[%s] adv2=[%s]" % \
                (tc, inf, neg, adv1, adv2)

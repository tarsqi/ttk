"""Implements the behaviour of chunks.

Chunks are embedded in sentences and contain event tags, timex tags and
instances of Token.

Much of the functionality of Evita and Slinket is delegated to chunks.

"""

import types
from xml.sax.saxutils import quoteattr

import library.forms as forms
import library.patterns as patterns
from library.main import LIBRARY

from components.common_modules import utils
from components.common_modules.constituent import Constituent

from components.evita.event import Event
from components.evita.features import NChunkFeatures, VChunkFeaturesList
from components.evita import wordnet
from components.evita import bayes

from components.evita.settings import INCLUDE_PROPERNAMES
from components.evita.settings import EVITA_NOM_DISAMB
from components.evita.settings import EVITA_NOM_CONTEXT
from components.evita.settings import EVITA_NOM_WNPRIMSENSE_ONLY

from utilities import logger


# Get the Bayesian event recognizer
nomEventRec = bayes.get_classifier()

# This is another way of capturing messages. It is separate from the logger and
# operates class based. It is used in VerbChunk to collect data from a run.
DRIBBLE = False

# Local throw-away debugging
DEBUG = False


EVENTID = LIBRARY.timeml.EVENTID
EIID = LIBRARY.timeml.EIID
CLASS = LIBRARY.timeml.CLASS
FORM = LIBRARY.timeml.FORM
STEM = LIBRARY.timeml.STEM
POS = LIBRARY.timeml.POS
TENSE = LIBRARY.timeml.TENSE
ASPECT = LIBRARY.timeml.ASPECT
EPOS = LIBRARY.timeml.EPOS
MOD = LIBRARY.timeml.MOD
POL = LIBRARY.timeml.POL
ORIGIN = LIBRARY.timeml.ORIGIN

NOUNCHUNK = LIBRARY.timeml.NOUNCHUNK
VERBCHUNK = LIBRARY.timeml.VERBCHUNK


def update_event_checked_marker(constituent_list):
    """Update Position in sentence, by marking as already checked for EVENT the
    Tokens and Chunks in constituent_list. These are constituents that are
    included in a chunk where an event was found."""
    for item in constituent_list:
        item.setCheckedEvents()


class Chunk(Constituent):

    """Implements the common behaviour of chunks. Chunks are embedded in sentences
    and contain event tags, timex tags and tokens.

    Instance variables (in addition to the ones defined on Constituent)
       phraseType         - string indicating the chunk type, either 'vg' or 'ng'
       head = -1          - the index of the head of the chunk
       features = None    - an instance of NChunkFeatures or VChunkFeatures
       features_list = [] - a list of VChunkFeatures, used for verb chunks
       event = None       - set to True if the chunk contains an event
       eid = None         - set to an identifier if the chunk contains an event
       eiid = None        - set to an identifier if the chunk contains an event
       checkedEvents = False

    Some of these variables are set to a non-default value at initialization,
    but most of them are filled in during processing. The variables event, eid
    and eiid are generated during TarsqiTree construction, they are all None
    when a tree is created for Evita, but can have values for components later
    in the pipeline."""

    # TODO: maybe replace eid and eiid with event_tag (cf AdjectiveToken)
    # TODO: the matcher may rely on event being 1 instead of True, check that

    def __init__(self, phraseType):
        # the constituent sets tree, parent, position, dtrs, begin, and end
        Constituent.__init__(self)
        self.phraseType = phraseType
        self.name = phraseType
        self.head = -1
        self.features = None
        self.features_list = []
        self.event = None
        self.eid = None
        self.eiid = None
        self.checkedEvents = False

    def feature_value(self, name):
        """Used by the matcher and needs cases for all instance variables used in the
        pattern matching phase. A similar method is used on Token."""
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
                return self.tree.events[self.eid].get(MOD, 'NONE')
            if name == POL:
                return self.tree.events[self.eid].get(POL, 'POS')
            if name == POS:
                return self.tree.events[self.eid].get(POS, 'NONE')
            return self.tree.events[self.eid][name]
        else:
            raise AttributeError(name)

    def getHead(self):
        """Return the head of the chunk (by default the last element)."""
        return self.dtrs[self.head]

    def _conditionally_add_imported_event(self, imported_event):
        """Create an event from the imported event, mixing information found in
        the chunk and in the imported event. Added from the imported event is
        the class (which means we potentially move away from the TimeML event
        classes) and the begin and end of the imported event which we store in
        the new 'full-range' feature, which is needed because Evita assumes
        events are all one-token."""
        # TODO: this is ad hoc and should be a bit more principled
        event = Event(self.features)
        event.attrs[CLASS] = imported_event.attrs['class']
        event.attrs[ORIGIN] += '-import'
        begin, end = imported_event.begin, imported_event.end
        full_text = self.tree.tarsqidoc.sourcedoc.text[begin:end]
        event.attrs['full-range'] = "%s-%s" % (begin, end)
        event.attrs['full-event'] = "%s" % quoteattr(full_text)
        self.tree.addEvent(event)

    def _conditionallyAddEvent(self, features=None):
        """Perform a few little checks on the head and check whether there is
        an event class, then add the event to the tree. When this is called on
        a NounChunk, then there is no GramChunk handed in and it will be
        retrieved from the features instance variable, when it is called from
        VerbChunk, then the verb's features will be handed in."""
        # TODO: split those cases to make for two simpler methods
        logger.debug("Conditionally adding nominal")
        chunk_features = self.features if features is None else features
        if self._acceptable_chunk_features(chunk_features):
            self.tree.addEvent(Event(chunk_features))

    @staticmethod
    def _acceptable_chunk_features(chunk_features):
        """Preform some simple tests to check whether the chunk features are acceptable
        for an event. The second and third tests seem relevant for verbs only, but we
        keep # them anyway for all chunks."""
        text = chunk_features.head.getText()
        return (chunk_features.evClass
                and text not in forms.be
                and text not in forms.spuriousVerb)

    def _getHeadText(self):
        """Get the text string of the head of the chunk. Used by
        matchConstituent."""
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
        print "%s<%s position=%s %d-%d checkedEvents=%s event=%s eid=%s>" % \
            (indent * ' ', self.__class__.__name__, self.position,
             self.begin, self.end, self.checkedEvents, self.event, self.eid)
        for tok in self.dtrs:
            tok.pretty_print(indent + 2)


class NounChunk(Chunk):

    """Behaviour specific to noun chunks, most notably the NounChunk specific
    code to create events."""

    def __init__(self):
        # the constituent sets tree, parent, position, dtrs, begin, and end
        Chunk.__init__(self, NOUNCHUNK)

    def isNounChunk(self):
        """Returns True"""
        return True

    def isDefinite(self):
        """Return True if self includes a Token that is a POS, PRP$ or a definite
        determiner."""
        for token in self.dtrs[:self.head]:
            # sometimes the daughter is not a token but a timex, skip it
            if not token.isToken():
                continue
            if (token.pos == forms.possessiveEndingTag or
                token.pos == forms.possessivePronounTag or
                (token.pos in forms.determinerTags and
                 token.getText() in forms.definiteDeterminers)):
                return True
        return False

    def isEmpty(self):
        """Return True if the chunk is empty, False otherwise."""
        return False if self.dtrs else True

    def createEvent(self, verbfeatures=None, imported_events=None):
        """Try to create an event in the NounChunk. Checks whether the nominal
        is an event candidate, then conditionally adds it. The verbfeatures
        dictionary is used when a governing verb hands in its features to a
        nominal in a predicative complement. The imported_events is handed in
        when Tarsqi tries to import events from a previous annotation."""
        logger.debug("NounChunk.createEvent(verbfeatures=%s)" % verbfeatures)
        if self.isEmpty():
            # this happened at some point due to a crazy bug in some old code
            # that does not exist anymore, log a warning in case this returns
            logger.warn("There are no dtrs in the NounChunk")
        else:
            self.features = NChunkFeatures(self, verbfeatures)
            logger.debug(self.features.as_verbose_string())
            # don't bother if the head already is an event
            if self.features.head.isEvent():
                logger.debug("Nominal already contains an event")
            # Even if preceded by a BE or a HAVE form, only tagging NounChunks
            # headed by an eventive noun, so "was an intern" will NOT be tagged
            elif self._passes_syntax_test():
                imported_event = self._get_imported_event_for_chunk(imported_events)
                #print imported_event
                if imported_event is not None:
                    self._conditionally_add_imported_event(imported_event)
                elif self._passes_semantics_test():
                    self._conditionallyAddEvent()

    def _passes_syntax_test(self):
        """Return True if the nominal is syntactically able to be an event,
        return False otherwise. An event candidate syntactically has to have a
        head which cannot be a timex and the head has to be a either a noun or a
        common noun, depending on the value of INCLUDE_PROPERNAMES."""
        if self.features.head.isTimex():
            return False
        if INCLUDE_PROPERNAMES:
            return self.head_is_noun()
        else:
            return self.head_is_common_noun()
        #return (not self.features.head.isTimex() and self.head_is_common_noun())

    def _passes_semantics_test(self):
        """Return True if the nominal can be an event semantically. Depending
        on user settings this is done by a mixture of wordnet lookup and using a
        simple classifier."""
        logger.debug("event candidate?")
        lemma = self.features.head_lemma
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

    def _get_imported_event_for_chunk(self, imported_events):
        """Return None or a Tag from the imported_events dictionary, only return
        this tag is its span is head final to the chunk and it span is at least
        including the chunk head."""
        # TODO: we now miss multiple events in a chunk
        if imported_events is None:
            imported_events = {}
        offsets = range(self.begin, self.end)
        # Get the tags for all characters in the entire span and then get the
        # head of the list, that is, the contiguous sequence of Tags at the end
        # of the range.
        tags = [imported_events.get(off) for off in offsets]
        imported_head = self._consume_head(tags)
        chunk_head = self.dtrs[self.head]
        chunk_head_length = chunk_head.end - chunk_head.begin
        if 0 < len(imported_head) >= chunk_head_length:
            return imported_head[0]
        else:
            return None

    @staticmethod
    def _consume_head(tags):
        head = []
        for t in reversed(tags):
            if t is None:
                return list(reversed(head))
            head.append(t)
        return list(reversed(head))

    def head_is_noun(self):
        """Returns True if the head of the chunk is a noun."""
        return forms.RE_nouns.match(self.features.head.pos)

    def head_is_common_noun(self):
        """Returns True if the head of the chunk is a common noun."""
        # using the regular expression is a bit faster then lookup in the short
        # list of common noun parts of speech (forms.nounsCommon)
        return forms.RE_nounsCommon.match(self.features.head.pos)

    def _run_classifier(self, lemma):
        """Run the classifier on lemma, using features from the GramNChunk."""
        features = []
        if EVITA_NOM_CONTEXT:
            features = ['DEF' if self.isDefinite() else 'INDEF',
                        self.features.head.pos]
        is_event = nomEventRec.isEvent(lemma, features)
        logger.debug("  nomEventRec.isEvent(%s) ==> %s" % (lemma, is_event))
        return is_event


class VerbChunk(Chunk):

    if DRIBBLE:
        DRIBBLE_FH = open("dribble-VerbChunk.txt", 'w')

    def __init__(self):
        # the constituent sets tree, parent, position, dtrs, begin, and end
        Chunk.__init__(self, VERBCHUNK)

    def dribble(self, header, text):
        """Write information on the sentence that an event was added to."""
        if DRIBBLE:
            toks = utils.get_tokens(self.parent.dtrs)
            p1 = toks[0].begin
            p2 = toks[-1].end
            e_p1 = self.dtrs[-1].begin
            e_p2 = self.dtrs[-1].end
            text = ' '.join(text.split())
            sentence = self.tree.tarsqidoc.sourcedoc.text[p1:p2]
            sentence = ' '.join(sentence.split())
            line = "%s\t%s\t%s\t%s:%s\n" % (header, text, sentence, e_p1, e_p2)
            VerbChunk.DRIBBLE_FH.write(line)

    def isVerbChunk(self):
        """Return True."""
        return True

    def isNotEventCandidate(self, features):
        """Return True if the chunk cannot possibly be an event. This is the place
        for performing some simple stoplist-like tests."""
        # TODO: why would any of these ever occur?
        # TODO: if we use a stop list it should be separated from the code
        return ((features.headForm == 'including' and features.tense == 'NONE')
                or features.headForm == '_')

    def createEvent(self, imported_events=None):
        """Try to create one or more events in the VerbChunk. How this works
        depends on how many instances of VChunkFeatures can be created for
        the chunk. For all non-final and non-axiliary elements in the list,
        just process them as events. For the chunk-final one there is more work
        to do."""
        vcf_list = VChunkFeaturesList(verbchunk=self)
        _debug_vcf(vcf_list)
        vcf_list = [vcf for vcf in vcf_list if vcf.is_wellformed()]
        if vcf_list:
            for vcf in vcf_list[:-1]:
                if not vcf.isAuxVerb():
                    self._conditionallyAddEvent(vcf)
            if not self.isNotEventCandidate(vcf_list[-1]):
                self._createEventOnRightmostVerb(vcf_list[-1], imported_events)

    def _createEventOnRightmostVerb(self, features, imported_events=None):
        next_node = self.next_node()
        if features.is_modal() and next_node:
            self._createEventOnModal()
        elif features.is_be() and next_node:
            self._createEventOnBe(features, imported_events)
        elif features.is_have():
            self._createEventOnHave(features)
        elif features.is_future_going_to():
            self._createEventOnFutureGoingTo(features)
        elif features.is_past_used_to():
            self._createEventOnPastUsedTo(features)
        elif features.is_do_auxiliar():
            self._createEventOnDoAuxiliar(features)
        elif features.is_become() and next_node:
            self._createEventOnBecome(features)
        elif features.is_continue() and next_node:
            self._createEventOnContinue(features)
        elif features.is_keep() and next_node:
            self._createEventOnKeep(features)
        else:
            self._createEventOnOtherVerb(features)

    def _createEventOnModal(self):
        """Try to create an event when the head of the chunk is a modal. Check
        the right context and see if you can extend the chunk into a complete
        verb group with modal verb and main verb. If so, process the merged
        constituents as a composed verb chunk."""
        # NOTE: this does not tend to apply since the chunker usually groups the
        # modal in with the rest of the verb group.
        logger.debug("Checking for modal pattern...")
        substring = self._lookForMultiChunk(patterns.MODAL_FSAs)
        if substring:
            self.dribble("MODAL", self.getText())
            self._processEventInMultiVChunk(substring)

    def _createEventOnBe(self, features, imported_events=None):
        logger.debug("Checking for BE + NOM Predicative Complement...")
        substring = self._lookForMultiChunk(patterns.BE_N_FSAs, 'chunked')
        if substring:
            self.dribble("BE-NOM", self.getText())
            self._processEventInMultiNChunk(features, substring, imported_events)
        else:
            logger.debug("Checking for BE + ADJ Predicative Complement...")
            substring = self._lookForMultiChunk(patterns.BE_A_FSAs, 'chunked')
            if substring:
                matched_texts = [s.getText() for s in substring]
                matched = self.getText() + ' ' + ' '.join(matched_texts)
                self.dribble("BE-ADJ", matched)
                self._processEventInMultiAChunk(features, substring)
            else:
                logger.debug("Checking for BE + VERB Predicative Complement...")
                substring = self._lookForMultiChunk(patterns.BE_FSAs)
                if substring:
                    self.dribble("BE-V", self.getText())
                    self._processEventInMultiVChunk(substring)

    def _createEventOnHave(self, features):
        logger.debug("Checking for toHave pattern...")
        substring = self._lookForMultiChunk(patterns.HAVE_FSAs)
        if substring:
            self.dribble("HAVE-1", self.getText())
            self._processEventInMultiVChunk(substring)
        else:
            self.dribble("HAVE-2", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnFutureGoingTo(self, features):
        logger.debug("Checking for futureGoingTo pattern...")
        substring = self._lookForMultiChunk(patterns.GOINGto_FSAs)
        if substring:
            self.dribble("GOING-TO", self.getText())
            self._processEventInMultiVChunk(substring)
        else:
            self.dribble("GOING", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnPastUsedTo(self, features):
        logger.debug("Checking for pastUsedTo pattern...")
        substring = self._lookForMultiChunk(patterns.USEDto_FSAs)
        if substring:
            self.dribble("USED-1", self.getText())
            self._processEventInMultiVChunk(substring)
        else:
            self.dribble("USED-2", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnDoAuxiliar(self, features):
        logger.debug("Checking for doAuxiliar pattern...")
        substring = self._lookForMultiChunk(patterns.DO_FSAs)
        if substring:
            self.dribble("DO-AUX", self.getText())
            self._processEventInMultiVChunk(substring)
        else:
            self.dribble("DO", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnBecome(self, features):
        # Looking for BECOME + ADJ Predicative Complement e.g., He became famous at
        # the age of 21
        logger.debug("Checking for BECOME + ADJ Predicative Complement...")
        substring = self._lookForMultiChunk(patterns.BECOME_A_FSAs, 'chunked')
        if substring:
            self.dribble("BECOME-ADJ", self.getText())
            self._processDoubleEventInMultiAChunk(features, substring)
        else:
            self.dribble("BECOME", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnContinue(self, features):
        # Looking for CONTINUE + ADJ Predicative Complement e.g., Interest rate
        # continued low.
        logger.debug("Checking for CONTINUE + ADJ...")
        substring = self._lookForMultiChunk(patterns.CONTINUE_A_FSAs, 'chunked')
        if substring:
            self.dribble("CONTINUE-ADJ", self.getText())
            self._processDoubleEventInMultiAChunk(features, substring)
        else:
            self.dribble("CONTINUE", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnKeep(self, features):
        # Looking for KEEP + ADJ Predicative Complement e.g., The announcement
        # kept everybody Adj.
        logger.debug("Checking for KEEP + [NChunk] + ADJ...")
        substring = self._lookForMultiChunk(patterns.KEEP_A_FSAs, 'chunked')
        if substring:
            self.dribble("KEEP-N-ADJ", self.getText())
            self._processDoubleEventInMultiAChunk(features, substring)
        else:
            self.dribble("KEEP", self.getText())
            self._conditionallyAddEvent(features)

    def _createEventOnOtherVerb(self, features):
        self.dribble("OTHER", self.getText())
        logger.debug("General case")
        self._conditionallyAddEvent(features)

    def _lookForMultiChunk(self, FSA_set, structure_type='flat'):
        """Returns the prefix of the rest of the sentence is it matches one of
        the FSAs in FSA_set. The structure_type argument specifies the
        structural format of the rest of the sentence: either a flat,
        token-level representation or a chunked one. This method is used for
        finding specific right contexts of verb chunks."""
        logger.debug("Entering _lookForMultiChunk for '%s' with %d FSAs"
                     % (self.getText().strip(), len(FSA_set)))
        logger.debug("\tstructure_type = %s" % structure_type)
        restSentence = self._getRestSent(structure_type)
        logger.debug("\trest = %s"
                     % ' '.join([t.__class__.__name__ for t in restSentence]))
        logger.debug("\trest = %s"
                     % ' '.join(["%s/%s" % (t.getText(), t.pos)
                                 for t in utils.get_tokens(restSentence)]))
        lenSubstring, fsaNum = self._identify_substring(restSentence, FSA_set)
        if lenSubstring:
            logger.debug("\tACCEPTED by FSA %d, LENGTH=%d" % (fsaNum, lenSubstring))
            return restSentence[:lenSubstring]
        else:
            logger.debug("\tREJECTED by all FSAs")
            return 0

    def _getRestSent(self, structure_type):
        """Obtain the rest of the sentence as a list of tokens if structure_type is
        'flat' and as a list of constituents if structure type is 'chunked'. Log a
        warning and return a list of constituents for an unknown structure type."""
        if structure_type == 'flat':
            restSentence = utils.get_tokens(self.parent[self.position + 1:])
        elif structure_type == 'chunked':
            restSentence = self.parent[self.position + 1:]
            if structure_type != 'chunked':
                logger.warn("unknown structure type: %s" % structure_type)
        return restSentence

    def _identify_substring(self, sentence_slice, fsa_list):
        """Similar to Constituent._identify_substring(), except that this method
        calls acceptsSubstringOf() instead of acceptsShortestSubstringOf(). In
        some tests, for example in evita-test2.sh, this version results in a
        small number of extra events."""
        # TODO: figure out when this one is used and when the one on Constituent
        # TODO: when there is a Slinket regression test, see what happens when
        # we remove this one --> NOTHING
        fsaCounter = -1
        if not isinstance(fsa_list, types.ListType):
            # TODO: this happens for example when Slinket processes "I was
            # delighted to see advertised.", find out why, once we do, we can
            # remove this method and just have the one on Constituent
            logger.warn("fsa_list is not a list, skipping")
            return (0, fsaCounter)
        for fsa in fsa_list:
            fsaCounter += 1
            lenSubstring = fsa.acceptsSubstringOf(sentence_slice)
            if lenSubstring:
                if DEBUG:
                    print "Succesful application of %s" % fsa.fsaname
                return (lenSubstring, fsaCounter)
        else:
            return (0, fsaCounter)

    def _processEventInMultiVChunk(self, substring):
        token_list = utils.get_tokens(self) + substring
        verbfeatureslist = VChunkFeaturesList(tokens=token_list)
        GramMultiVChunk = verbfeatureslist[0]
        self._conditionallyAddEvent(GramMultiVChunk)
        map(update_event_checked_marker, substring)

    def _processEventInMultiNChunk(self, features, substring, imported_events):
        nounChunk = substring[-1]
        nounChunk.createEvent(features, imported_events)
        map(update_event_checked_marker, substring)

    def _processEventInMultiAChunk(self, features, substring):
        adjToken = substring[-1]
        adjToken.createAdjEvent(features)
        map(update_event_checked_marker, substring)

    def _processDoubleEventInMultiAChunk(self, features, substring):
        """Tagging EVENT in both VerbChunk and AdjectiveToken. In this case the
        adjective will not be given the verb features."""
        logger.debug("[V_2Ev] " + features.as_verbose_string())
        self._conditionallyAddEvent(features)
        adjToken = substring[-1]
        adjToken.createAdjEvent()
        map(update_event_checked_marker, substring)


def _debug_vcf(vcf_list):
    logger.debug("len(features_list) = %d" % len(vcf_list))
    if len(vcf_list) > 0 and DEBUG:
        for vcf in vcf_list:
            print ' ',
            vcf.pp()
    for vcf in vcf_list:
        logger.debug(vcf.as_verbose_string())

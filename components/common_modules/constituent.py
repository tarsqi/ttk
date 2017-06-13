from types import ListType, TupleType
from pprint import pprint

from utilities import logger
from library.main import LIBRARY


class Constituent:

    """An abstract class that contains some methods that are identical for Chunks
    and Tokens plus a couple of default methods.

    Instance variables:
       tree     -  the TarsqiTree instance that the constituent is an element of
       parent   -  the parent, could be any non-token constituent
       position -  index in the parent's daughters list
       dtrs     -  a list of Tokens, EventTags and TimexTags
       begin    -  beginning offset in the SourceDoc
       end      -  ending offset in the SourceDoc
       tag      -  the tag that the Constituent was created from

    On initialization these are all set to None or the empty list (for the dtrs
    variabe). All values are filled in when the TarsqiTree is created from a
    docelement Tag.

    """

    def __init__(self):
        self.tree = None
        self.parent = None
        self.position = None
        self.dtrs = []
        self.begin = None
        self.end = None
        self.tag = None

    def __setitem__(self, index, val):
        """Sets a value on the dtrs variable."""
        self.dtrs[index] = val

    def __getitem__(self, index):
        """Returns an element from the dtrs variable."""
        return self.dtrs[index]

    def __iter__(self):
        return iter(self.dtrs)

    def __reversed__(self):
        return reversed(self.dtrs)

    def __nonzero__(self):
        return True

    def __cmp__(self, other):
        # NOTE: in some cases the matchLabel method in FSA.py checks for
        # equality of a constituent and a string using == in which case this
        # method is invoked, which would throw an error without the first two
        # lines
        if isinstance(other, type('')):
            return 1
        return cmp(self.begin, other.begin)

    def __len__(self):
        """Returns the lenght of the dtrs variable."""
        # NOTE. When you have this method you want __nonzero__ as well because
        # without it a constituent with an empty dtrs list will be False and
        # this will cause errors, should probbaaly consider adding an __eq__
        # magic method
        return len(self.dtrs)

    def __str__(self):
        return "<%s %d:%d>" % (self.__class__.__name__, self.begin, self.end)

    def includes(self, tag):
        """Returns True if tag is positioned inside the consituent."""
        return self.begin <= tag.begin and self.end >= tag.end

    def overlaps(self, tag):
        """Returns True if tag overlaps with the constituent."""
        return (self.begin <= tag.begin <= self.end
                or self.begin <= tag.end <= self.end
                or tag.begin <= self.begin <= tag.end
                or tag.begin <= self.end <= tag.end)

    def feature_value(self, name):
        """Used by matchConstituent. Needs cases for all instance variables used
        in the pattern matching phase."""
        print name
        if name == 'nodeType':
            return self.__class__.__name__
        elif name == 'text':
            return None
        elif name == 'pos':
            return None
        else:
            raise AttributeError(name)

    def isSentence(self):
        return False

    def isToken(self):
        return False

    def isAdjToken(self):
        return False

    def isChunk(self):
        return False

    def isVerbChunk(self):
        return False

    def isNounChunk(self):
        return False

    def isTimex(self):
        return False

    def isEvent(self):
        return False

    def isPreposition(self):
        return False

    def all_nodes(self, result=None):
        """Returns all nodes through a pre-order tree search."""
        if result is None:
            result = []
        result.append(self)
        for dtr in self.dtrs:
            dtr.all_nodes(result)
        return result

    def leaf_nodes(self, result=None):
        """Returns the leaf nodes of the constituent."""
        if result is None:
            result = []
        if not self.dtrs:
            result.append(self)
        for dtr in self.dtrs:
            dtr.leaf_nodes(result)
        return result

    def first_leaf_node(self):
        """Return the first leaf node in the constituent."""
        if self.dtrs:
            return self.dtrs[0].first_leaf_node()
        else:
            return self

    def path_to_top(self):
        """Return the path to the top, but do not include the top and the node
        itself."""
        path = []
        node = self
        while node is not None:
            path.append(node)
            node = node.parent
        return path[1:-1]

    def syntax(self):
        """Return a string that contains the category names of all intermediate
        elements from the constituent to the top."""
        return '-'.join([c.name for c in self.path_to_top()])

    def events(self):
        """Return all events in the constituent."""
        return [n for n in self.all_nodes() if n.isEvent()]

    def timexes(self):
        """Return all timexes in the constituent."""
        return [n for n in self.all_nodes() if n.isTimex()]

    def setCheckedEvents(self):
        if self.parent.__class__.__name__ == 'Sentence':
            self.checkedEvents = True
        else:
            self.parent.setCheckedEvents()

    def getText(self):
        string = ""
        for dtr in self.dtrs:
            string += ' ' + dtr.getText()
        return string

    def next_node(self):
        """Return the next sibling in the tree or None if there is none. If this
        is called on the last dtr in a constituent, then it returns the next
        sibling of the parent. Returns None if self is a rightmost
        constituent."""
        node = self
        while node is not None:
            if node.position + 1 < len(node.parent.dtrs):
                return node.parent[node.position + 1]
            else:
                node = node.parent
        return None

    def createEvent(self, imported_events=None):
        """Does nothing except for logging a warning. If this happens something
        unexpected is going on. Event creation is only attempted on some sub
        classes."""
        logger.warn("Unexpected recipient of createEvent()")

    def matchConstituent(self, description):

        """Match the chunk instance to the patterns in description, which is a
        dictionary with keys-values pairs that match instance variables and
        their values on the constituent.

        The value in key-value pairs can be:
        - an atomic value. E.g., {..., 'headForm':'is', ...}
        - a list of possible values. E.g., {..., headForm': forms.have, ...}
          In this case, matchConstituent checks whether the chunk feature is
          included within this list.
        - a negated value. It is done by introducing it as
          a second constituent of a 2-position tuple whose initial position
          is the caret symbol: '^'. E.g., {..., 'headPos': ('^', 'MD') ...}

        This is a specialized version of the matchDict method in utilities/FSA.py
        and it is intended to deal with Chunks and Tokens."""

        # this operates by trying to find a failed match, only if there is no
        # such thing the method will return True
        for feat in description.keys():
            value = description[feat]
            if type(value) is TupleType:
                if value[0] == '^':
                    if type(value[1]) is ListType:
                        if self.feature_value(feat) in value[1]:
                            return False
                    else:
                        if self.feature_value(feat) == value[1]:
                            return False
                else:
                    raise "ERROR specifying description of pattern"
            elif type(value) is ListType:
                if self.feature_value(feat) not in value:
                    if self.isChunk() and feat == 'text':
                        if self._getHeadText() not in value:
                            return False
                    else:
                        return False
            else:
                if self.feature_value(feat) != value:
                    return False
        return True

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

    def print_vars(self):
        pprint(vars(self))

    def pretty_print(self):
        print "<<pretty_print() not defined for this object>>"

    # SLINKET METHODS
    # There is some serious redundancy here, refactor these methods.

    def find_forward_alink(self, fsa_reltype_groups):
        """Search for an alink to the right of the event. Return True
        is event was found, False otherwise."""
        logger.debug("len(fsa_reltype_groups) = %s" % len(fsa_reltype_groups))
        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        alinkedEventContext = self.parent[self.position + 1:]
        return self._find_alink(alinkedEventContext, fsa_lists, reltypes_list)

    def find_backward_alink(self, fsa_reltype_groups):
        """Search for an alink to the left of the event. Return True is event
        was found, False otherwise. Note that the context includes the event
        itself and the token to its immediate right. It is not quite clear why
        but it has tro do with how the patterns are defined.

        Backward Alinks also check for the adequacy (e.g., in terms of TENSE or
        ASPECT) of the Subordinating Event. For cases such as 'the
        <EVENT>transaction</EVENT> has been <EVENT>completed</EVENT>'"""

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        alinkedEventContext = self.parent[:self.position + 1]
        alinkedEventContext.reverse()
        return self._find_alink(alinkedEventContext, fsa_lists, reltypes_list)

    def _find_alink(self, event_context, fsa_lists, reltype_list):
        """Try to create an alink using the context and patterns from the
        dictionary. Alinks are created as a side effect. Returns True if an
        alink was created, False otherwise."""

        for i in range(len(fsa_lists)):

            fsa_list = fsa_lists[i]
            result = self._look_for_link(event_context, fsa_lists[i])
            if result:
                (length_of_match, fsa_num) = result
                fsa = fsa_list[fsa_num]
                # logger.debug("match found, FSA=%s size=%d reltype=%s"
                #           % (fsa.fsaname, length_of_match, reltype))
                reltype = get_reltype(reltype_list, i)
                eiid = event_context[length_of_match - 1].eiid
                # print self, self.eiid
                alinkAttrs = {
                    LIBRARY.timeml.EVENT_INSTANCE_ID: self.eiid,
                    LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE: eiid,
                    LIBRARY.timeml.RELTYPE: reltype,
                    LIBRARY.timeml.SYNTAX: fsa.fsaname }
                self.tree.addLink(alinkAttrs, LIBRARY.timeml.ALINK)
                # for l in self.tree.alink_list: print '  ', l
                logger.debug("ALINK CREATED")
                return True
            else:
                logger.debug("REJECTED ALINK by FSA: " + str(i))

        return False

    def find_forward_slink(self, fsa_reltype_groups):
        """Tries to create forward Slinks, using a group of FSAs.

        Arguments:
           fsa_reltype_groups -
               a list of two lists, the first list is a list of fsa
               lists, the second list is a list of relation types
               [ [ [fsa, fsa, ...], [fsa, fsa, ...], ...],
                 [ reltype, reltype, ... ] ] """

        logger.debug("len(fsa_reltype_groups) = %s" % len(fsa_reltype_groups))
        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        event_context = self.parent[self.position + 1:]
        return self._find_slink(event_context, fsa_lists, reltypes_list)

    def find_backward_slink(self, fsa_reltype_groups):
        """Tries to create backward Slinks, using a group of FSAs.  Backward
        Slinks should check for the adequacy (e.g., in terms of TENSE or ASPECT)
        of the Subordinating Event. For cases such as 'the
        <EVENT>transaction</EVENT> has been <EVENT>approved</EVENT>'

        Arguments:
           fsa_reltype_groups - see createForwardSlinks """

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        event_context = self.parent[:self.position + 1]
        event_context.reverse()
        return self._find_slink(event_context, fsa_lists, reltypes_list)

    def find_reporting_slink(self, fsa_reltype_groups):
        """Reporting Slinks are applied to reporting predicates ('say', 'told',
        etc) that link an event in a preceeding quoted sentence which is
        separated from the clause of the reporting event by a comma; e.g.,

            ``I <EVENT>want</EVENT> a referendum,'' Howard
            <EVENT class='REPORTING'>said</EVENT>.

        Slinket assumes that these quoted clauses always initiate the main
        sentence. Therefore, the first item in the sentence are quotation
        marks."""

        fsa_lists = fsa_reltype_groups[0]
        reltypes_list = fsa_reltype_groups[1]
        sentenceBeginning = self.parent[:self.position]
        if len(sentenceBeginning) > 0 and sentenceBeginning[0].getText() == "``":
            # quotation does not contain quotation marks
            quotation = self._extract_quotation(sentenceBeginning)
            if quotation is not None:
                logger.debug("TRYING reporting slink")
                return self._find_slink(quotation, fsa_lists, reltypes_list)
        return False

    def _find_slink(self, event_context, fsa_lists, reltype_list):
        """Try to find an slink in the given event_context using lists of
        FSAs. If the context matches an FSA, then create an slink and insert it
        in the tree."""

        for i in range(len(fsa_lists)):

            fsa_list = fsa_lists[i]
            result = self._look_for_link(event_context, fsa_list)
            if result:
                (length_of_match, fsa_num) = result
                fsa = fsa_list[fsa_num]
                # logger.debug("match found, FSA=%s size=%d reltype=%s"
                #           % (fsa.fsaname, length_of_match, reltype))
                reltype = get_reltype(reltype_list, i)
                eiid = event_context[length_of_match - 1].eiid
                slinkAttrs = {
                    LIBRARY.timeml.EVENT_INSTANCE_ID: self.eiid,
                    LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE: eiid,
                    LIBRARY.timeml.RELTYPE: reltype,
                    LIBRARY.timeml.SYNTAX: fsa.fsaname }
                self.tree.addLink(slinkAttrs, LIBRARY.timeml.SLINK)
                logger.debug("SLINK CREATED")
                return True
            else:
                logger.debug("REJECTED SLINK by FSA: " + str(i))

        return False

    def _look_for_link(self, sentence_slice, fsa_list):
        """Given a slice of a sentence and a list of FSAs, return a tuple of the
        size of the matching slize and the number of the FSA that featured in
        the match. Return False if there is no match."""
        lenSubstring, fsaNum = self._identify_substring(sentence_slice, fsa_list)
        if lenSubstring:
            return (lenSubstring, fsaNum)
        else:
            return False

    def _identify_substring(self, sentence_slice, fsa_list):
        """Checks whether sentence_slice, a sequence of chunks and tokens,
        matches one of the FSAs in fsa_list. Returns a tuple of the sub sequence
        length that matched the pattern (where a zero length indicates no match)
        and the index of the FSA that returned the match."""
        fsaCounter = -1
        for fsa in fsa_list:
            logger.debug("Applying FSA %s" % fsa.fsaname)
            fsaCounter += 1
            # We first used acceptsShortestSubstringOf(), now we use the longest
            # match. The latter gave a marginally better result, but this was
            # only apparent on one Slink in the Slink regression test so more
            # tests may be needed.
            lenSubstring = fsa.acceptsSubstringOf(sentence_slice)
            if lenSubstring:
                logger.debug("FSA %s matched" % fsa.fsaname)
                return (lenSubstring, fsaCounter)
        return (0, fsaCounter)

    def _extract_quotation(self, fragment):
        # TODO: this is a bit messy
        for idx in range(len(fragment)):
            try:
                # For some reason, it may break here (though rarely)
                if (fragment[idx].getText() == "''" and
                    (fragment[idx - 1].getText() == "," or
                     fragment[idx + 1].getText() == ",")):
                    return fragment[1:idx]
            except:
                logger.warn('Quotation could not be extracted')
        else:
            return


def get_reltype(reltype_list, i):
    """Returns the reltype in reltype_list at index i. Returns the last element of
    reltype list if i is out of bounds (which happens when patterns have a list
    of reltypes that is shorter than the list of FSAs."""
    try:
        reltype = reltype_list[i]
    except IndexError:
        # TODO: why would this happen?
        reltype = reltype_list[-1]
    return reltype

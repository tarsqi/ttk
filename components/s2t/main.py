"""
Main module for the S2T component.

Responsible for the top-level processing of S2T. It contains Slink2Tlink, which
inherits from TarsqiComponent as well as Slink, a class that takes care of
applying s2t-rules to each SLINK.

"""

from utilities import logger
from components.common_modules.component import TarsqiComponent
from library.tarsqi_constants import S2T
from library.s2t import s2t_rule_loader
from library.main import LIBRARY


class Slink2Tlink (TarsqiComponent):

    """Implements the S2T component of Tarsqi. S2T takes the output of Slinket
    and applies rules to the Slinks to create new Tlinks."""

    def __init__(self):
        """Set component name and load rules into an S2TRuleDictionary object."""
        self.NAME = S2T
        self.doctree = None
        self.docelement = None
        self.rules = s2t_rule_loader.read_rules()

    def process_doctree(self, doctree):
        """Apply all S2T rules to doctree."""
        self.doctree = doctree
        # For sanity we clean out the tlinks since we are adding new tlinks to
        # the document, if we don't do this we might add some links twice.
        self.doctree.tlinks = []
        self.docelement = self.doctree.docelement
        events = self.doctree.tarsqidoc.tags.find_tags(LIBRARY.timeml.EVENT)
        eventsIdx = dict([(e.attrs['eiid'], e) for e in events])
        for slinktag in self.doctree.slinks:
            slink = Slink(self.doctree, eventsIdx, slinktag)
            try:
                slink.match_rules(self.rules)
            except:
                logger.error("S2T Error when processing Slink instance")
        self._add_links_to_tarsqidoc()

    def _add_links_to_tarsqidoc(self):
        """Export the links from the TarsqiTree to the TagRepository instance on
        the TarsqiDocument. We do this because the match code inserts into the
        tarsqi tree, but we may want to revisit this and do it the same way as
        Blinker, which adds directly to the TarsqiDocument."""
        for tlink in self.doctree.tlinks:
            tagname = LIBRARY.timeml.TLINK
            logger.debug("Adding %s: %s" % (tagname, tlink.attrs))
            self.doctree.tarsqidoc.tags.add_tag(tagname, -1, -1, tlink.attrs)


class Slink:

    """Implements the Slink object. An Slink object consists of the attributes
    of the SLINK (relType, eventInstanceID, and subordinatedEventInstance) and
    the attributes of the specific event instances involved in the link.

    Instance variables:
       doctree - a TarsqiTree
       attrs - adictionary containing the attributes of the slink
       eventInstance - an InstanceTag
       subEventInstance - an InstanceTag"""

    def __init__(self, doctree, instances, slinkTag):
        """Initialize an Slink using an XMLDocument, a dictionary of instances
        and the slink element from xmldoc."""
        self.doctree = doctree
        self.attrs = slinkTag.attrs
        eiid1 = self.attrs[LIBRARY.timeml.EVENT_INSTANCE_ID]
        eiid2 = self.attrs[LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE]
        self.eventInstance = instances[eiid1]
        self.subEventInstance = instances[eiid2]

    def __str__(self):
        return "<Slink %s>" % self.attrs

    def match_rules(self, rules):
        """Match all the rules in the rules argument to the SLINK. If a rule
        matches, this method creates a TLINK and breaks out of the loop."""
        for rule in rules:
            result = self.match(rule)
            if result:
                self.create_tlink(rule)
                break

    def match(self, rule):
        """ The match method applies an S2TRule object to an the Slink. It
        returns the rule if the Slink is a match, False otherwise."""
        for (attr, val) in rule.attrs.items():
            # relType must match
            if attr == 'reltype':
                if (val != self.attrs['relType']):
                    return False
            # relation is the rhs of the rule, so need not match
            elif attr == 'relation':
                continue
            # all other features are features on the events in the SLINK, only
            # consider those that are on event and subevent.
            elif '.' in attr:
                (event_object, attribute) = attr.split('.')
                if event_object == 'event':
                    if (val != self.eventInstance.attrs.get(attribute)):
                        return False
                elif event_object == 'subevent':
                    if (val != self.subEventInstance.attrs.get(attribute)):
                        return False
        return rule

    def create_tlink(self, rule):
        """Takes an S2T rule object and calls the add_tlink method from xmldoc
        to create a new TLINK using the appropriate SLINK event instance IDs and
        the relation attribute of the S2T rule."""
        EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
        RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
        SUBORDINATED_EVENT_INSTANCE= LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE
        tlinkAttrs = {
            EVENT_INSTANCE_ID: self.attrs[EVENT_INSTANCE_ID],
            RELATED_TO_EVENT_INSTANCE: self.attrs[SUBORDINATED_EVENT_INSTANCE],
            LIBRARY.timeml.RELTYPE: rule.attrs['relation'],
            LIBRARY.timeml.ORIGIN: S2T,
            LIBRARY.timeml.SYNTAX: "RULE-%s" % rule.id }
        self.doctree.addLink(tlinkAttrs, LIBRARY.timeml.TLINK)


class Alink:

    # TODO: needs complete overhaul and needs to be done in another component

    def __init__(self, xmldoc, doctree, alinkTag):
        self.xmldoc = xmldoc
        self.doctree = doctree
        self.attrs = alinkTag.attrs

    def lookForAtlinks(self):
        """Examine whether the Alink can generate a Tlink."""
        if self.is_a2t_candidate():
            logger.debug("A2T Alink candidate " + self.attrs['lid'] + " " +
                         self.attrs['relType'])
            apply_patterns(self)
        else:
            logger.debug("A2T Alink not a candidate " + self.attrs['lid'] +
                         " " + self.attrs['relType'])

    def is_a2t_candidate(self):
        reltype = a2tCandidate.attrs['relType']
        return reltype in ('INITIATES', 'CULMINATES', 'TERMINATES')

    def apply_patterns(self):
        """Loop through TLINKs to match A2T pattern"""
        logger.debug("SELF Properties:")
        logger.debug(self.attrs['lid'] + " " + self.attrs['eventInstanceID'] +
                     " " + self.attrs['relatedToEventInstance'] +
                     " " + self.attrs['relType'])
        for tlink in self.doctree.alink_list:
            logger.debug("Current TLINK ID: " + tlink.attrs['lid'])
            if 'relatedToTime' not in tlink.attrs and 'timeID' not in tlink.attrs:
                if self.attrs['eventInstanceID'] == tlink.attrs['eventInstanceID']:
                    logger.debug("Matched TLINK Properties:")
                    logger.debug(tlink.attrs['lid']
                                 + " " + tlink.attrs['eventInstanceID']
                                 + " " + tlink.attrs['relatedToEventInstance']
                                 + " " + tlink.attrs['relType'])
                    createTlink(self, tlink, 1)
                elif self.attrs['eventInstanceID'] == tlink.attrs['relatedToEventInstance']:
                    logger.debug("Matched TLINK Properties:")
                    logger.debug(tlink.attrs['lid']
                                 + " " + tlink.attrs['eventInstanceID']
                                 + " " + tlink.attrs['relatedToEventInstance']
                                 + " " + tlink.attrs['relType'])
                    self.createTlink(tlink, 2)
                else:
                    logger.debug("No TLINK match")
            else:
                logger.debug("TLINK with Time, no match")

    def createTlink(self, tlink, patternNum):
        if patternNum == 1:
            logger.debug("Pattern Number: " + str(patternNum))
            self.xmldoc.add_tlink(tlink.attrs['relType'],
                                  self.attrs['relatedToEventInstance'],
                                  tlink.attrs['relatedToEventInstance'],
                                  'A2T_rule_' + str(patternNum))
        elif patternNum == 2:
            logger.debug("Pattern Number: " + str(patternNum))
            self.xmldoc.add_tlink(tlink.attrs['relType'],
                                  tlink.attrs['eventInstanceID'],
                                  self.attrs['relatedToEventInstance'],
                                  'A2T_rule_' + str(patternNum))

"""
Main module for the S2T component. 

Responsible for the top-level processing of S2T. It contains
Slink2Tlink, which inherits from TarsqiComponent as well as Slink, a
class that takes care of applying s2t-rules to each SLINK.

"""

#from docmodel.xml_parser import Parser
from utilities import logger
from components.common_modules.component import TarsqiComponent
from library.tarsqi_constants import S2T
from library.s2t import s2t_rule_loader
from library.timeMLspec import EVENT_INSTANCE_ID
from library.timeMLspec import SUBORDINATED_EVENT_INSTANCE


class Slink2Tlink (TarsqiComponent):

    """Implements the S2T component of Tarsqi.
    S2T takes the output of the Slinket component and applies rules to the
    Slinks to create new Tlinks.

    Instance variables:
       NAME - a string
       rules - a list of S2TRules"""

    def __init__(self):
        """Set component name and load rules into an S2TRuleDictionary object.
        This object knows where the rules are stored."""
        self.NAME = S2T
        self.rules = s2t_rule_loader.read_rules()

    def process_file(self, infile, outfile):
        """Apply all S2T rules to the input file.  Parses the xml file with
        xml_parser.Parser and converts it using FragmentConverter. Then calls
        createTLinksFromSlinks."""
        xmlfile = open(infile, "r")
        self.xmldoc = Parser().parse_file(xmlfile)
        self.createTLinksFromSLinks()
        self.xmldoc.save_to_file(outfile)

    def process_xmldoc(self, xmldoc):
        """Apply all S2T rules to xmldoc. Creates a Document object using
        FragmentConverter (the only reason this is done is to get easy
        access to the Alinks and Slinks). Then calls
        createTLinksFromSlinks."""
        self.xmldoc = xmldoc
        self.createTLinksFromSLinks()

    def createTLinksFromALinks(self):
        """Calls alink.lookForAtlinks to add Tlinks from Alinks. This is
        rather moronic unfortunately because it will never do anything
        because at the time of application there are no tlinks in the
        document. Needs to be separated out and apply at a later
        processing stage, after all other tlinking."""
        for alinkTag in self.doctree.alink_list:
            try:
                alink = Alink(self.xmldoc, self.doctree, alinkTag)
                alink.lookForAtlinks()
            except:
                logger.error("Error processing ALINK")

    def createTLinksFromSLinks(self):
        """Calls lookForStlinks for a given Slink object."""
        instances = {}
        for inst in self.xmldoc.get_tags('MAKEINSTANCE'):
            instances[inst.attrs['eiid']] = inst
        for el in self.xmldoc.get_tags('SLINK'):
            try:
                slink = Slink(self.xmldoc, instances, el)
                slink.match_rules(self.rules)
            except:
                logger.error("Error processing SLINK")


class Slink:

    """Implements the Slink object. An Slink object consists of the
    attributes of the SLINK (relType, eventInstanceID, and
    subordinatedEventInstance) and the attributes of the specific
    event instances involved in the link.

    Instance variables:
       xmldoc - an XmlDocument
       attrs - adictionary containing the attributes of the slink
       eventInstance - an InstanceTag
       subEventInstance - an InstanceTag"""

    def __init__(self, xmldoc, instances, slinkTag):
        """Initialize an Slink using an XMLDocument, a dictionary of
        instances and the slink element from xmldoc."""
        self.xmldoc = xmldoc
        self.attrs = slinkTag.attrs
        eiid1 = self.attrs[EVENT_INSTANCE_ID]
        eiid2 = self.attrs[SUBORDINATED_EVENT_INSTANCE]
        self.eventInstance = instances[eiid1]
        self.subEventInstance = instances[eiid2]

    def match_rules(self, rules):
        """Match all the rules in the rules argument to the SLINK. If a rule
        matches, this method creates a TLINK and returns. There is no
        return value."""
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
            # all other features are features on the events in the
            # SLINK, only consider those that are on event and
            # subevent.
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
        to create a new TLINK using the appropriate SLINK event
        instance IDs and the relation attribute of the S2T rule."""
        self.xmldoc.add_tlink(rule.attrs['relation'],
                              self.attrs[EVENT_INSTANCE_ID],
                              self.attrs[SUBORDINATED_EVENT_INSTANCE],
                              'S2T Rule ' + rule.id)


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
            logger.debug("A2T Alink not a candidate " + self.attrs['lid'] + " " +
                         self.attrs['relType'])
            
    def is_a2t_candidate(self):
        if a2tCandidate.attrs['relType'] in ('INITIATES', 'CULMINATES', 'TERMINATES'):
            return True
        else:
            return False

    def apply_patterns(self):
        """Loop through TLINKs to match A2T pattern"""
        logger.debug("SELF Properties:")
        logger.debug(self.attrs['lid'] + " " + self.attrs['eventInstanceID']
                     + " " + self.attrs['relatedToEventInstance']
                     + " " + self.attrs['relType'])
        
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

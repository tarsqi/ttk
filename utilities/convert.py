"""convert.py

Some format conversion utilities. Run all commands below from the parent
directory using the -m option.

1. Convert LDC TimeBank into a modern TimeBank in the TTK format.

   $ python -m utilities.convert --timebank2ttk TIMEBANK_DIR TTK_DIR

   Converts TimeBank 1.2 as released by LDC into a version without makeinstance
   tags using the TTK format. This should be run on the data/extra files in the
   LDC distribution because those have the metadata that allow the TimeBank meta
   data parser to find the DCT.

2. Convert Thyme format into TTK.

   $ python -m utilities.convert --thyme2ttk THYME_TEXT_DIR THYME_ANNO_DIR TTK_DIR

   Note that in the Thyme corpus we have annotation directories like
   AnnotationData/coloncancer/Dev, whereas in the text directories we find
   TextData/dev. The latter will have more files than the former. Files in
   THYME_TEXT_DIR but not in THYME_ANNO_DIR will be ignored.

3. Convert the TTK format into HTML.

   $ python -m utilities.convert --ttk2html TTK_DIR HTML_DIR
   $ python -m utilities.convert --ttk2html --show-links TTK_DIR HTML_DIR

   Converts TTK files in TTK_DIR into HTML files in HTML_DIR, if --show-links is
   used links are shown in addition to the timexes and events.

4. Convert Knowtator format into TTK.

   $ python -m utilities.convert --knowtator2ttk KNOWTATOR_DIR TTK_DIR
   $ python -m utilities.convert --knowtator2ttk --tarsqi KNOWTATOR_DIR TTK_DIR

   This is not a general conversion from any Knowtator output, it assumes that
   the input annotations are all events, timexes and tlinks. If the --tarsqi
   option is used then the event tags are put in the tarsqi_tags repository, by
   default they are put in the source_tags repository (that is, they are not
   considered Tarsqi results), using the --tarsqi option can be useful for
   evaluation.

   $ python -m utilities.convert --knowtator2ttk --tarsqi TEXT_FILE TTK_FILE

   Version for processing a single file. You only supply the text file, the code
   assumes that there is a file TEXT_FILE.knowtator.xml with the annotations.

5. Convert TTK into Knowtator format.

   $ python -m utilities.convert --ttk2knowtator TTK_FILE TEXT_FILE ANNO_FILE

   IN PROGRESS.

6. Convert from ECB into TTK

   $ python -m utilities.convert --ecb2ttk ECB_DIR OUT_DIR

   THE ECB_DIR directory should be the top-level directory of the ECB
   distribution (which has a README file and a data directory which includes
   directories for each topic). Converted files are written to OUT_DIR, the
   structure of which mirrors the structure of the ECB directory. Each TTK file
   written to the output has the topic id as a metadata property as well as a
   couple of MENTION tags in the source_tags section. These mentions tend to be
   Evita events, but are impoverished in the sense that they only have three
   attributes: begin, end and chain. The idea is that the information in
   mentions will be merged with information in events.

   Will at some point also include the ECB+ data.

"""

from __future__ import absolute_import, print_function, unicode_literals

import os, sys, getopt, codecs, time, glob
from xml.dom import minidom, Node

import tarsqi
from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser
from docmodel.document import TarsqiDocument, Tag, ProcessingStep
from library.main import TarsqiLibrary
from io import open

DEBUG = True
DEBUG = False

LIBRARY = TarsqiLibrary()

TIMEX = LIBRARY.timeml.TIMEX
EVENT = LIBRARY.timeml.EVENT
SIGNAL = LIBRARY.timeml.SIGNAL
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK

LID = LIBRARY.timeml.LID
TID = LIBRARY.timeml.TID
EID = LIBRARY.timeml.EID
EIID = LIBRARY.timeml.EIID
EVENTID = LIBRARY.timeml.EVENTID

RELTYPE = LIBRARY.timeml.RELTYPE
TIME_ID = LIBRARY.timeml.TIME_ID
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
SUBORDINATED_EVENT_INSTANCE = LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE

MAKEINSTANCE = 'MAKEINSTANCE'

TIMEML_TAGS = (TIMEX, EVENT, MAKEINSTANCE, SIGNAL, ALINK, SLINK, TLINK)


### CONVERTING TIMEBANK INTO TTK

def convert_timebank(timebank_dir, out_dir):
    """Take the LDC TimeBank files in timebank_dir and create timebank files in
    out_dir that are in the TTK format and do not have MAKEINSTANCE tags."""
    # make the paths absolute so we do not get bitten by Tarsqi's habit of
    # changing the current directory
    timebank_dir = os.path.abspath(timebank_dir)
    out_dir = os.path.abspath(out_dir)
    _makedir(out_dir)
    for fname in os.listdir(timebank_dir):
        if fname.endswith('.tml'):
            print(fname)
            _convert_timebank_file(os.path.join(timebank_dir, fname),
                                   os.path.join(out_dir, fname))
            break

def _convert_timebank_file(infile, outfile):
    tarsqidoc = _get_tarsqidoc(infile, "timebank")
    for tagname in TIMEML_TAGS:
        tarsqidoc.tags.import_tags(tarsqidoc.sourcedoc.tags, tagname)
        tarsqidoc.sourcedoc.tags.remove_tags(tagname)
    events = tarsqidoc.tags.find_tags(EVENT)
    instances = tarsqidoc.tags.find_tags(MAKEINSTANCE)
    instances = { i.attrs.get(EVENTID): i for i in instances }
    for event in events:
        instance = instances[event.attrs[EID]]
        del instance.attrs[EVENTID]
        event.attrs.update(instance.attrs)
    tarsqidoc.tags.remove_tags(MAKEINSTANCE)
    tarsqidoc.print_all(outfile)


### CONVERTING THYME INTO TTK

def convert_thyme(thyme_text_dir, thyme_anno_dir, out_dir, limit=sys.maxsize):
    thyme_text_dir = os.path.abspath(thyme_text_dir)
    thyme_anno_dir = os.path.abspath(thyme_anno_dir)
    out_dir = os.path.abspath(out_dir)
    _makedir(out_dir)
    count = 0
    for fname in os.listdir(thyme_anno_dir):
        count += 1
        if count > limit:
            break
        thyme_text_file = os.path.join(thyme_text_dir, fname)
        out_file = os.path.join(out_dir, fname)
        # in the annotations the file is actually a directory of annotations
        anno_files = os.listdir(os.path.join(thyme_anno_dir, fname))
        timeml_files = [f for f in anno_files if f.find('Temporal') > -1]
        if timeml_files:
            #if not fname == "ID090_clinic_265": continue
            #if not fname == "ID090_path_266a": continue
            print(fname)
            thyme_anno_file = os.path.join(thyme_anno_dir, fname, timeml_files[0])
            try:
                _convert_thyme_file(thyme_text_file, thyme_anno_file, out_file)
            except:
                print("WARNING: error on %s" % fname)


def _convert_thyme_file(thyme_text_file, thyme_anno_file, out_file):
    LinkID.reset()
    tarsqidoc = _get_tarsqidoc(thyme_text_file, "text")
    dom = minidom.parse(thyme_anno_file)
    entities = [Entity(e) for e in dom.getElementsByTagName('entity')]
    relations = [Relation(r) for r in dom.getElementsByTagName('relation')]
    doctimes = [e for e in entities if e.type == 'DOCTIME']
    sectiontimes = [e for e in entities if e.type == 'SECTIONTIME']
    events = [e for e in entities if e.type == 'EVENT']
    timexes = [e for e in entities if e.type == 'TIMEX3']
    alinks = [r for r in relations if r.type == 'ALINK']
    tlinks = [r for r in relations if r.type == 'TLINK']
    event_idx = {}
    timex_idx = {}
    metadata = {'dct': None}
    timexes = doctimes + sectiontimes + timexes
    _add_timexes_to_tarsqidoc(timexes, timex_idx, metadata, tarsqidoc)
    _add_events_to_tarsqidoc(events, event_idx, metadata['dct'], tarsqidoc)
    _add_links_to_tarsqidoc(alinks + tlinks, timex_idx, event_idx, tarsqidoc)
    tarsqidoc.print_all(out_file)


def _add_timexes_to_tarsqidoc(timexes, timex_idx, metadata, tarsqidoc):
    for timex in timexes:
        try:
            begin, end = timex.span.split(',')
            if timex.id in timex_idx:
                print("WARNING: timex %s already exists" % timex.id)
            timex_idx[timex.id] = begin
            attrs = { TID: timex.id }
            if timex.type == 'DOCTIME':
                metadata['dct'] = timex
                attrs['functionInDocument'] = 'DOCTIME'
                doctime = tarsqidoc.text(int(begin), int(end))
                month, day, year = doctime.split('/')
                dct_value = "%04d%02d%02d" % (int(year), int(month), int(day))
                tarsqidoc.metadata['dct'] = dct_value
            elif timex.type == 'SECTIONTIME':
                attrs['functionInDocument'] = 'SECTIONTIME'
            tarsqidoc.sourcedoc.tags.add_tag('TIMEX3', begin, end, attrs)
        except ValueError:
            print("Skipping discontinuous timex")


def _add_events_to_tarsqidoc(events, event_idx, dct, tarsqidoc):
    """Add an event from the Thyme file. Also includes adding a TLINK to the DCT,
    for this link we generate a new link identifier."""
    dct_rel_id = 0
    for event in events:
        try:
            begin, end = event.span.split(',')
            if event.id in event_idx:
                print("WARNING: event %s already exists" % event.id)
            event_idx[event.id] = begin
            # TODO: is it okay for these to be the same?
            attrs = { EID: event.id, EIID: event.id}
            tarsqidoc.sourcedoc.tags.add_tag('EVENT', begin, end, attrs)
            dct_rel_id += 1
            if dct is not None:
                attrs = { LID: next(LinkID), #LID: next(LinkID),
                          RELTYPE: event.DocTimeRel,
                          EVENT_INSTANCE_ID: event.id,
                          RELATED_TO_TIME: dct.id }
                tarsqidoc.sourcedoc.tags.add_tag('TLINK', None, None, attrs)
        except ValueError:
            print("Skipping discontinuous event")


def _add_links_to_tarsqidoc(links, timex_idx, event_idx, tarsqidoc):
    """Add a link from the Thyme file. Inherit the identifier on the Thyme
    relation, even though it does not adhere to TimeML id formatting."""
    for rel in links:
        linkid = "r%s" % rel.id.split('@')[0]
        sourceid = "%s%s" % (rel.Source.split('@')[1], rel.Source.split('@')[0])
        targetid = "%s%s" % (rel.Target.split('@')[1], rel.Target.split('@')[0])
        attrs = {
            LID: linkid,
            _source_attr_name(rel.type, sourceid, timex_idx, event_idx): sourceid,
            _target_attr_name(rel.type, targetid, timex_idx, event_idx): targetid,
            RELTYPE: rel.RelType}
        tarsqidoc.sourcedoc.tags.add_tag(rel.type, None, None, attrs)


def _source_attr_name(link_type, source_id, timex_idx, event_idx):
    if link_type == ALINK:
        return EVENT_INSTANCE_ID
    elif source_id in timex_idx:
        return TIME_ID
    elif source_id in event_idx:
        return EVENT_INSTANCE_ID
    else:
        print("WARNING: cannot find attribute name for %s" % source_id)


def _target_attr_name(link_type, target_id, timex_idx, event_idx):
    if link_type == ALINK:
        return RELATED_TO_EVENT_INSTANCE
    elif target_id in timex_idx:
        return RELATED_TO_TIME
    elif target_id in event_idx:
        return RELATED_TO_EVENT_INSTANCE
    else:
        print("WARNING: cannot find attribute name for %s" % target_id)


class Entity(object):

    """An entity from a Thyme annotation, either an event or a timex (note that
    a timex can be a DOCTIME or SECTIONTIME type)."""

    def __init__(self, dom_element):
        self.id = get_simple_value(dom_element, 'id')
        self.span = get_simple_value(dom_element, 'span')
        self.type = get_simple_value(dom_element, 'type')
        self.properties = get_value(dom_element, 'properties')
        self.id = "%s%s" % (self.id.split('@')[1], self.id.split('@')[0])
        if self.type == EVENT:
            self.DocTimeRel = get_simple_value(self.properties, 'DocTimeRel')
            self.Polarity = get_simple_value(self.properties, 'Polarity')
        elif self.type == TIMEX:
            self.Class = get_simple_value(self.properties, 'Class')

    def __str__(self):
        if self.type == EVENT:
            return "<%s id=%s span=%s DocTimeRel=%s Polarity=%s>" % \
                (self.type, self.id, self.span, self.DocTimeRel, self.Polarity)
        elif self.type == TIMEX:
            return "<%s id=%s span=%s Class=%s>" % \
                (self.type, self.id, self.span, self.Class)
        else:
            return "<%s id=%s span=%s>" % \
                (self.type, self.id, self.span)


class Relation(object):

    def __init__(self, dom_element):
        self.id = get_simple_value(dom_element, 'id')
        self.type = get_simple_value(dom_element, 'type')
        self.properties = get_value(dom_element, 'properties')
        self.Source = get_simple_value(self.properties, 'Source')
        self.RelType = get_simple_value(self.properties, 'Type')
        self.Target = get_simple_value(self.properties, 'Target')

    def __str__(self):
        return "<%s id=%s %s(%s,%s)>" % \
            (self.type, self.id, self.RelType, self.Source, self.Target)


class LinkID(object):

    """Class to provide fresh identifiers for TLINK tags."""

    # TODO: should probably combine this with TagID in the preprocessor wrapper

    IDENTIFIER = 0

    @classmethod
    def next(cls):
        cls.IDENTIFIER += 1
        return "l%d" % cls.IDENTIFIER

    @classmethod
    def reset(cls):
        cls.IDENTIFIER = 0


def get_value(entity, attr):
    return entity.getElementsByTagName(attr)[0]


def get_simple_value(entity, attr):
    return entity.getElementsByTagName(attr)[0].firstChild.data


### CONVERTING KNOWTATOR INTO TTK

class KnowtatorConverter(object):

    """Class responsible for converting two Knowtator files (a text file and an
    annotation file) into a TTK file."""

    def __init__(self, text_file=None, annotation_file=None, ttk_file=None):
        """Initialize input and output file names. The input is a text file and
        annotation file, the put is a ttk file. If no annotation file name is
        given, it will be created from the text file name using the default
        extentions."""
        self.text_file = os.path.abspath(text_file)
        self.ttk_file = os.path.abspath(ttk_file)
        if annotation_file is None:
            self.anno_file = self.text_file + '.knowtator.xml'
        else:
            self.anno_file = os.path.abspath(annotation_file)

    def convert(self, tarsqi_tags):
        """Reads the knowtator data and saves them as a TTK file."""
        self.read()
        self.export(tarsqi_tags)

    def read(self):
        """Read all annotations and put all information (including attributes and
        relations) in the annotations instance variable."""
        self.dom = minidom.parse(self.anno_file)
        self._read_annotations()
        self._read_stringSlotMentions()
        self._read_classMentions()
        self._read_complexSlotMention()
        self._enrich_annotations()

    def _read_annotations(self):
        """Reads the annotation tags, which ontain the identifier, character offsets and
        the text."""
        self.annotations = {}
        for ann_dom in self.dom.getElementsByTagName('annotation'):
            annotation = KnowtatorAnnotation(ann_dom)
            self.annotations[annotation.mention_id] = annotation

    def _read_stringSlotMentions(self):
        """Reads the stringSlotMention tags, which contain the attributes."""
        self.string_slot_mentions = {}
        for ssm_dom in self.dom.getElementsByTagName('stringSlotMention'):
            ssm = KnowtatorStringSlotMention(ssm_dom)
            self.string_slot_mentions[ssm.mention_id] = ssm

    def _read_classMentions(self):
        """Reads the classMention tags, which have the class (tagname) and links to
        attributes and relations."""
        self.class_mentions = {}
        for cm_dom in self.dom.getElementsByTagName('classMention'):
            cm = KnowtatorClassMention(cm_dom)
            self.class_mentions[cm.mention_id] = cm

    def _read_complexSlotMention(self):
        """Reads the complexSlotMention tags, which contain the relations."""
        self.complex_slot_mentions = {}
        for csm_dom in self.dom.getElementsByTagName('complexSlotMention'):
            csm = KnowtatorComplexSlotMention(csm_dom)
            self.complex_slot_mentions[csm.mention_id] = csm

    def _enrich_annotations(self):
        """Adds information from other tags to the annotation tags."""
        for cm in self.class_mentions.values():
            anno = self.annotations[cm.mention_id]
            anno.classname = cm.classname
            for sm in cm.slot_mentions:
                ssm = self.string_slot_mentions.get(sm)
                if ssm is not None:
                    # add the attributes
                    anno.attributes[ssm.att] = ssm.val
                else:
                    # add the relations
                    csm = self.complex_slot_mentions.get(sm)
                    anno.relations.append([csm.attribute, csm.csm_value])

    def export(self, tarsqi_tags):
        """Saves all annotations in a TTK file."""
        tarsqidoc = _get_tarsqidoc(self.text_file, "text")
        for annotation in self.annotations.values():
            tags = []
            tag = annotation.as_ttk_tag()
            tags.append(tag)
            for rel in annotation.relations:
                att1 = 'timeID' if annotation.classname == 'Timex3' else 'eventID'
                val1 = tag.attrs.get('tid', tag.attrs.get('eiid'))
                target = self.annotations[rel[1]]
                target_tag = target.as_ttk_tag()
                att2 = RELATED_TO_TIME
                if target_tag.name == EVENT:
                    att2 = RELATED_TO_EVENT_INSTANCE
                val2 = target_tag.attrs.get(TID, target_tag.attrs.get(EIID))
                feats = { 'relType': rel[0], att1: val1, att2: val2 }
                tags.append(Tag(TLINK, -1, -1, feats))
            tagrepo = tarsqidoc.tags if tarsqi_tags else tarsqidoc.sourcedoc.tags
            for t in tags:
                tagrepo.append(t)
        tarsqidoc.print_all(self.ttk_file)

    def pretty_print(self):
        for annotation in sorted(self.annotations.values()):
            print()
            annotation.pretty_print()

    def pp_csms(self):
        for key in sorted(self.complex_slot_mentions):
            print(self.complex_slot_mentions[key])

    def pp_ssms(self):
        for key in sorted(self.string_slot_mentions):
            print(self.string_slot_mentions[key])

    def pp_cms(self):
        for key in sorted(self.class_mentions):
            print(self.class_mentions[key])


class KnowtatorAnnotation(object):

    """Implements the object for <annotation> tags, which contain just the text
    span, but enriches them with information from the other tags. Instance
    variables are:

       mention_id  - unique id, taken from the id attribute of the mention tag
       start       - from start attribute of span tag
       end         - from end attribute of span tag
       text        - cdata of spannedText tag
       classname   - taken from the classMention tag
       attributes  - taken from the classMention and stringSlotMention tags
       relations   - taken from the classMention and complexSlotMention tags

    Here is an example of an annotation XML tag:
    
       <annotation>
           <mention id="EHOST_Instance_95" />
           <annotator id="eHOST_2010">Ruth</annotator>
           <span start="27" end="45" />
           <spannedText>September 29, 2005</spannedText>
           <creationDate>Fri Jul 07 14:17:59 CDT 2017</creationDate>
       </annotation>

    """

    @classmethod
    def tag(cls, tag_identifier, tag, spanned_text):
        """This acts as a factory method that given some arguments creates an XML string
        for a Knowtator annotation tag."""
        return \
            '<annotation>\n' + \
            '    <mention id="EHOST_Instance_%s" />\n' % tag_identifier + \
            '    <annotator id="%s">TTK</annotator>\n' % open('VERSION').read().strip() + \
            '    <span start="%s" end="%s" />\n' % (tag.begin, tag.end) + \
            '    <spannedText>%s</spannedText>\n' % spanned_text + \
            '    <creationDate>%s</creationDate>\n' % time.strftime("%Y%m%d", time.localtime())+ \
            '</annotation>\n'

    def __init__(self, annotation):
        """Reads the relevant information from the DOM object. Assumes there is
        only one mention, span and spanned text."""
        mention = annotation.getElementsByTagName('mention')[0]
        span = annotation.getElementsByTagName('span')[0]
        text = annotation.getElementsByTagName('spannedText')[0]
        self.mention_id = mention.getAttribute('id')
        self.start = int(span.getAttribute('start'))
        self.end = int(span.getAttribute('end'))
        self.text = text.firstChild.data
        self.classname = None
        self.attributes = {}
        self.relations = []

    def __eq__(self, other):
        return self.start == other.start

    def __ne__(self, other):
        return self.start != other.start

    def __lt__(self, other):
        return self.start < other.start

    def __le__(self, other):
        return self.start <= other.start

    def __gt__(self, other):
        return self.start > other.start

    def __ge__(self, other):
        return self.start >= other.start

    def __str__(self):
        return "<annotation %s %s %s-%s '%s'>" \
            % (self.mention_id, self.classname, self.start, self.end, self.text)

    def as_ttk_tag(self):
        tagname = self.classname.upper()
        identifier = self.mention_id[15:]
        if tagname == 'EVENT':
            feats = { 'class': self.attributes['classType'],
                      'eid': 'e' + identifier,
                      'eiid': 'ei' + identifier }
        elif tagname == 'TIMEX3':
            # TODO: value is not the right format
            feats = { 'type': self.attributes['typeInfo'],
                      'value': self.attributes['value'],
                      'tid': 't' + identifier }
        else:
            feats = {}
        return Tag(tagname, self.start, self.end, feats)


    def pretty_print(self):
        print(self)
        for att, val in self.attributes.items():
            print("   %s=%s" % (att, val))
        for relType, target in self.relations:
            print("   %s %s" % (relType, target))


class KnowtatorClassMention(object):

    """Implements the objects for <classMention> tags, which contains the tag name
    and links annotations to attributes and relations. Fields are:

       mentiod_id    - value of the id attribute
       classname     - the id attribute of the mentionClass tag
       slot_mentions - list from the id attribute of the hasSlotMention tags

    A hasSlotMention tag points to either a stringSlotMention tag, which
    contains an attribute-value pair, or to a complexSlotMention, which contains
    a relation and points to an annotation. The classname is the tagname, for
    example 'Event'.

    XML example:

       <classMention id="EHOST_Instance_95">
           <hasSlotMention id="EHOST_Instance_110" />
           <hasSlotMention id="EHOST_Instance_111" />
           <mentionClass id="Timex3">September 29, 2005</mentionClass>
       </classMention>

    """

    @classmethod
    def tag(cls, tag_identifier, tag, mention_class, spanned_text, slot_mentions):
        """Factory method for creating MentionClass XML strings."""
        has_slot_mention_tags = []
        for sm in slot_mentions:
            has_slot_mention_tags.append(
                '<hasSlotMention id="EHOST_Instance_%s" />\n' % sm)
        return \
            '<classMention id="EHOST_Instance_%s">\n' % tag_identifier + \
            '    ' + '    '.join(has_slot_mention_tags) + \
            '    <mentionClass id="%s">%s</mentionClass>\n' % (mention_class, spanned_text) + \
            '</classMention>\n'

    def __init__(self, cm):
        self.mention_id = cm.getAttribute('id')
        mention_class = cm.getElementsByTagName('mentionClass')[0]
        slot_mentions = cm.getElementsByTagName('hasSlotMention')
        self.classname = mention_class.getAttribute('id')
        self.slot_mentions = [sm.getAttribute('id') for sm in slot_mentions]

    def __str__(self):
        return "<classMention %s %s %s>" \
            % (self.mention_id, self.classname, ' '.join(self.slot_mentions))


class KnowtatorStringSlotMention(object):

    """Implements the object for the <stringSlotMentionTag> tags, which contain
    attributes and their values. The fields are:

       mention_id - the value of the id attribute
       att        - the id attribute of the mentionSlot tag
       val        - the value attribute of the stringSlotMentionValue tag

   Example XML tag:

       <stringSlotMention id="EHOST_Instance_111">
           <mentionSlot id="value" />
           <stringSlotMentionValue value="09/29/2005" />
       </stringSlotMention>

       """

    @classmethod
    def tag(cls, identifier, attribute, value):
        """Factory method to generate an XML string for the stringSlotMention tag from
        an identifier, attribute and value."""
        return \
            '<stringSlotMention id="EHOST_Instance_%s">\n' % identifier + \
            '    <mentionSlot id="%s" />\n' % attribute + \
            '    <stringSlotMentionValue value="%s" />\n' % value + \
            '</stringSlotMention>\n'

    def __init__(self, ssm):
        """Reads a DOM Element with tagName=stringSlotMention."""
        mention_slot = ssm.getElementsByTagName('mentionSlot')[0]
        ssm_value = ssm.getElementsByTagName('stringSlotMentionValue')[0]
        self.mention_id = ssm.getAttribute('id')
        self.att = mention_slot.getAttribute('id')
        self.val = ssm_value.getAttribute('value')

    def __str__(self):
        return "<stringSlotMention %s %s=%s>" \
            % (self.mention_id, self.att, self.val)


class KnowtatorComplexSlotMention(object):

    """Implements the object for <complexSlotMention> tags, which contain the
    relations. Fields are:

       mention_slot - the id attribute of the mentionSlot tag
       attribute    - the cdata of the attribute tag
       csm_value    - the value attribute of the complexSlotMentionValue tag

    The id links back to the classMention which links this tag to an
    annotation. The attribute has an id (always TLINK for tlinks) and uses cdata
    for the value. The csm_value points to another annotation.

    XML tag example:
    
       <complexSlotMention id="EHOST_Instance_115">
           <mentionSlot id="TLINK" />
           <attribute id="relType">DURING</attribute>
           <complexSlotMentionValue value="EHOST_Instance_98" />
       </complexSlotMention>
    
    """

    @classmethod
    def tag(cls, identifier, reltype, target_identifier):
        """Factory method for complexSlotMention XML strings."""
        return \
            '<complexSlotMention id="EHOST_Instance_%s">\n' % identifier + \
            '    <mentionSlot id="TLINK" />\n' + \
            '    <attribute id="relType">%s</attribute>\n' % reltype + \
            '    <complexSlotMentionValue value="EHOST_Instance_%s" />\n' % target_identifier + \
            '</complexSlotMention>\n'
        
    def __init__(self, csm):
        self.mention_id = csm.getAttribute('id')
        mention_slot = csm.getElementsByTagName('mentionSlot')[0]
        attribute = csm.getElementsByTagName('attribute')[0]
        csm_value = csm.getElementsByTagName('complexSlotMentionValue')[0]
        self.mention_slot = mention_slot.getAttribute('id')
        self.attribute = attribute.firstChild.data
        self.csm_value = csm_value.getAttribute('value')

    def __str__(self):
        return "<complexSlotMention %s %s %s %s>" \
            % (self.mention_id, self.mention_slot, self.attribute, self.csm_value)


def convert_knowtator(knowtator_dir, ttk_dir, limit, tarsqi_tags=False):
    """Convert pairs of Knowtator files (source plus annotations) into single TTK
    files. This just takes care of figuring out the individual files in the
    directories and then lets KnowtatorCOnverter do the work."""
    knowtator_dir = os.path.abspath(knowtator_dir)
    ttk_dir = os.path.abspath(ttk_dir)
    _makedir(ttk_dir)
    count = 0
    # Read the list of file names. Note that with Knowtator we have a separate
    # annotation file in addition to the source file: for each source file named
    # 'file.txt' we also have an annotations file named 'file.txt.knowtator.xml'.
    fnames = os.listdir(knowtator_dir)
    fnames = [f for f in fnames if not f.endswith('knowtator.xml')]
    for fname in fnames:
        count += 1
        if count > limit:
            break
        print(fname)
        source_file = os.path.join(knowtator_dir, fname)
        anno_file = os.path.join(knowtator_dir, fname + '.knowtator.xml')
        # this assumes the .txt extension and replaces it with .ttk
        ttk_fname = fname[:-3] + 'ttk'
        ttk_file = os.path.join(ttk_dir, ttk_fname)
        converter = KnowtatorConverter(text_file=source_file,
                                       annotation_file=anno_file,
                                       ttk_file=ttk_file)
        converter.convert(tarsqi_tags)


### CONVERTING TTK INTO HTML

def convert_ttk_dir_into_html(ttk_dir, html_dir, showlinks, limit):
    ttk_dir = os.path.abspath(ttk_dir)
    html_dir = os.path.abspath(html_dir)
    _makedir(html_dir)
    print(ttk_dir)
    print(html_dir)
    index = open(os.path.join(html_dir, 'index.html'), 'w')
    count = 0
    for fname in os.listdir(ttk_dir):
        count += 1
        if count > limit:
            break
        ttk_file = os.path.join(ttk_dir, fname)
        html_file = os.path.join(html_dir, fname + '.html')
        index.write("<li><a href=%s.html>%s.html</a></li>\n" % (fname, fname))
        convert_ttk_file_into_html(ttk_file, html_file, showlinks)


def convert_ttk_file_into_html(ttk_file, html_file, showlinks):
    print("creating %s" % html_file)
    ttk_file = os.path.abspath(ttk_file)
    html_file = os.path.abspath(html_file)
    tarsqidoc = _get_tarsqidoc(ttk_file, "ttk")
    event_idx = _get_events(tarsqidoc)
    timex_idx = _get_timexes(tarsqidoc)
    entity_idx = _get_entities(event_idx, timex_idx)
    link_idx = _get_links(tarsqidoc)
    fh = _open_html_file(html_file)
    count = 0
    previous_was_space = False
    current_sources = []
    fh.write("<tr>\n<td>\n")
    for char in tarsqidoc.sourcedoc.text:
        if count in event_idx['close']:
            _write_closing_tags(event_idx, count, 'event', fh, showlinks)
        if count in timex_idx['close']:
            _write_closing_tags(timex_idx, count, 'timex', fh, showlinks)
        if count in event_idx['open']:
            _write_opening_tags(event_idx, count, 'event', fh)
            current_sources.append(event_idx['open'][count][0])
        if count in timex_idx['open']:
            _write_opening_tags(timex_idx, count, 'timex', fh)
            current_sources.append(timex_idx['open'][count][0])
        if char == "\n":
            if previous_was_space and showlinks and current_sources:
                fh.write("<tr><td width=40%>\n")
                for entity in current_sources:
                    identifier = 'tid' if  entity.name == 'TIMEX3' else 'eiid'
                    for link in link_idx.get(entity.attrs[identifier], []):
                        _write_link(link, entity_idx, fh)
                fh.write("\n<tr valign=top>\n<td>\n")
                previous_was_space = False
                current_sources = []
            else:
                fh.write("<br/>\n")
                previous_was_space = True
        else:
            fh.write(char)
        count += 1


def _get_events(tarsqidoc):
    """Return an index of events indexed on the begin and end offset."""
    events = tarsqidoc.tags.find_tags('EVENT')
    event_idx = {'open': {}, 'close': {}}
    for event in events:
        event_idx['open'].setdefault(event.begin, []).append(event)
        event_idx['close'].setdefault(event.end, []).append(event)
    return event_idx


def _get_timexes(tarsqidoc):
    """Return an index of times indexed on the begin and end offset."""
    timexes = tarsqidoc.tags.find_tags('TIMEX3')
    timex_idx = {'open': {}, 'close': {}}
    for timex in timexes:
        timex_idx['open'].setdefault(timex.begin, []).append(timex)
        timex_idx['close'].setdefault(timex.end, []).append(timex)
    return timex_idx


def _get_entities(event_idx, timex_idx):
    """Return an index of all entities indexed on the event or timex id."""
    entity_idx = {}
    for elist in list(event_idx['open'].values()) + list(timex_idx['open'].values()):
        entity = elist[0]
        identifier = 'tid' if  entity.name == 'TIMEX3' else 'eiid'
        entity_idx[entity.attrs[identifier]] = entity
    return entity_idx


def _get_links(tarsqidoc):
    links = {}
    for link in tarsqidoc.slinks() + tarsqidoc.tlinks():
        source = link.attrs.get('timeID') \
                 or link.attrs.get('eventInstanceID')
        target = link.attrs.get('relatedToTime') \
                 or link.attrs.get('relatedToEventInstance') \
                 or link.attrs.get('subordinatedEventInstance')
        if source is None: print("WARNING, no source for %s" % link)
        if target is None: print("WARNING, no target for %s" % link)
        links.setdefault(source, []).append([link.attrs['lid'], source,
                                             link.attrs['relType'], target])
    return links


def _open_html_file(html_file):
    fh = codecs.open(html_file, 'w', encoding="utf8")
    fh.write("<html>\n<body>\n" +
             "<style>\n" +
             "body { font-size: 14pt; }\n" +
             "sup { font-size: 10pt; font-weight: normal; }\n" +
             "td { padding-top: 10pt; }\n" +
             "event { xfont-weight: bold; color: darkred; }\n" +
             "timex { xfont-weight: bold; color: darkblue; }\n" +
             ".link { color: darkgreen; }\n" +
             "</style>\n" +
             "<body>\n" +
             "<table cellspacing=0 border=0>\n")
    return fh


def _write_event_close(event, fh, showlinks):
    if showlinks:
        fh.write("<sup>%s:%s</sup></event>" % (event.eid, event.begin))
    else:
        fh.write("<sup>%s</sup></event>" % event.eid)


def _write_closing_tags(idx, count, tagname, fh, showlinks):
    entities = idx['close'][count]
    for entity in reversed(entities):
        # for an identifier try the eid or tid
        identifier = entity.attrs.get('eid') or entity.attrs.get('tid')
        if showlinks:
            fh.write("<sup>%s:%s</sup></%s>]" % (identifier, entity.begin, tagname))
        else:
            #fh.write("<sup>%s</sup></%s>]" % (identifier, tagname))
            fh.write("<sup>%s</sup></%s>]" % (entity.begin, tagname))


def _write_opening_tags(idx, count, tagname, fh):
    entities = idx['open'][count]
    for entity in entities:
        fh.write("[<%s>" % tagname)


def _write_link(link, entity_idx, fh):
    link_id = link[0]
    reltype = link[2]
    source_id = link[1]
    target_id = link[3]
    source_entity = entity_idx.get(source_id)
    source_begin = source_entity.begin
    target_entity = entity_idx.get(target_id)
    target_begin = target_entity.begin
    fh.write("<span class=link id=%s>[%s:%s&nbsp;%s&nbsp;%s:%s]</span>\n"
             % (link_id, source_id, source_begin,
                reltype.lower(), target_id, target_begin))
    if target_entity is None:
        print("WARNING: %s %s %s %s" % (link_id, source_id, reltype, target_id))


### CONVERTING TTK FILE INTO KNOWTATOR FORMAT

def convert_ttk_into_knowtator(ttk_file, text_file, annotation_file):
    print("creating %s" % annotation_file)
    ttk_file = os.path.abspath(ttk_file)
    text_file = os.path.abspath(text_file)
    annotation_file = os.path.abspath(annotation_file)
    tarsqidoc = _get_tarsqidoc(ttk_file, "ttk")
    full_text = tarsqidoc.sourcedoc.text
    with codecs.open(text_file, 'w', encoding="utf-8") as text:
        text.write(full_text)
    with codecs.open(annotation_file, 'w', encoding="utf-8") as anno:
        anno.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        anno.write('<annotations textSource="%s">\n' % os.path.basename(text_file))
        tag_index = _create_tag_index(tarsqidoc.tags.tags)
        for tag in tarsqidoc.tags.tags:
            _knowtator_convert_tag(tag, tag_index, full_text, anno)
        anno.write('</annotations>\n')


def _create_tag_index(tags):
    """Create an index for the event and timex tags. The keys in this index are the
    eid or tid and the values are pairs of the tag itself and a list of tlinks for
    which this tag is a source."""
    tag_index = {}
    tlink_index = {}
    tlink_tags = []
    for tag in tags:
        tag_id = tag.get_identifier()
        if tag.name.upper() in (EVENT, TIMEX):
            tag_index[tag_id] = [tag]
        elif tag.name.upper() in (TLINK,):
            tlink_tags.append(tag)
    for tag in tlink_tags:
        source_identifier = tag.attrs.get(TIME_ID,
                                          tag.attrs.get(EVENT_INSTANCE_ID))
        tlink_index.setdefault(source_identifier, []).append(tag)
    for tag_identifier in tag_index:
        tlinks = tlink_index.get(tag_identifier, [])
        tag_index[tag_identifier].append(tlinks)
    #_print_tag_index(tag_index)
    return tag_index


def _print_tag_index(tag_index):
    for identifier in tag_index:
        print("%s\n   %s" % (identifier, tag_index[identifier][0]))
        for tlink in tag_index[identifier][1]:
            print ("   %s" % tlink)
    print()


def _knowtator_convert_tag(tag, tag_index, text, fh):
    """Take the Tag instance and generate Knowtator XML tags for it."""
    tag_id = tag.get_identifier()
    # only looping over events and timexes, link tags are derived from them
    if tag.name.upper() in {TIMEX, EVENT}:
        classname = tag.name
        string_slot_mentions = [(KnowtatorID.new_identifier(), attr, val)
                                for attr, val in tag.attrs.items()]
        spanned_text = text[tag.begin:tag.end]
        annotation = KnowtatorAnnotation.tag(tag_id, tag, spanned_text)
        ssm_tags = _knowtator_stringSlotMention_tags(string_slot_mentions)
        complex_slot_mentions = []
        # pull the links out of the index and create complex slot mentions for them
        for link in tag_index[tag_id][1]:
            target_id = link.attrs.get(RELATED_TO_EVENT_INSTANCE,
                                        link.attrs.get(RELATED_TO_TIME))
            complex_slot_mentions.append(
                (KnowtatorID.new_identifier(), link.attrs.get('relType'), target_id))
        csm_tags = _knowtator_complexSlotMention_tags(complex_slot_mentions)
        slot_mentions = [sm[0] for sm in string_slot_mentions + complex_slot_mentions]
        class_mention = KnowtatorClassMention.tag(
            tag_id, tag, classname, spanned_text, slot_mentions)
        fh.write(annotation + ''.join(ssm_tags) + ''.join(csm_tags) + class_mention)


def _knowtator_stringSlotMention_tags(string_slot_mentions):
    def ssm_tag(ssm):
        identifier, attribute, value = ssm
        return KnowtatorStringSlotMention.tag(identifier, attribute, value)
    return [ssm_tag(ssm) for ssm in string_slot_mentions]


def _knowtator_complexSlotMention_tags(complex_slot_mentions):
    def csm_tag(csm):
        identifier, reltype, target_id = csm
        return KnowtatorComplexSlotMention.tag(identifier, reltype, target_id)
    return [csm_tag(csm) for csm in complex_slot_mentions]


class KnowtatorID(object):
    """Just a class to generate identifiers."""
    identifier = 0
    @classmethod
    def new_identifier(cls):
        cls.identifier += 1
        return cls.identifier


### 6. CONVERT ECB INTO TTK

class ECBConverter(object):

    def __init__(self, ecb_directory, ttk_directory):
        """Collect specifications for each ECB file, which includes the ecb directory,
        the target directory (used to write converted files), the topic name and the
        filename (includes the topic name, for example "1/7.ecb)."""
        self.ecb_directory = ecb_directory
        self.ttk_directory = ttk_directory
        self.ecb_specs = []
        self.ecb_files = []
        self.topics = {}
        filepaths = glob.glob(os.path.join(self.ecb_directory, 'data', '*', '*.ecb'))
        for fp in filepaths:
            datadir, fname = os.path.split(fp)
            datadir, topic = os.path.split(datadir)
            fname = os.path.join(topic, fname)
            self.ecb_specs.append((ecb_directory, ttk_directory, topic, fname))

    def convert(self, topic=None):
        """Convert TTK files into ECB files. Use the topic argument to limit processing
        to one topic, the value can be an integer from 1 to 45 or a string representation
        of that integer."""
        if topic is not None:
            # turn the topic into a string if it isn't one yet
            topic = "%s" % topic
            specs = [spec for spec in self.ecb_specs if spec[2] == topic]
        else:
            specs = self.ecb_specs
        print("Converting %d files..." % len(specs))
        for (ecb_directory, ttk_directory, topic, fname) in specs:
            ecb_file = ECBFile(ecb_directory, ttk_directory, topic, fname)
            self.ecb_files.append(ecb_file)
            print("   %s" % ecb_file)
        self._populate_topics()
        self._write_files()

    def _write_files(self):
        for ecb_file in self.ecb_files:
            ecb_file.write()

    def _populate_topics(self):
        for ecb_file in self.ecb_files:
            self.topics.setdefault(ecb_file.topic, []).append(ecb_file)

    def print_topics(self):
        for topic, ecb_files in self.topics.items():
            print(topic)
            for ecb_file in ecb_files:
                print("   %s" % ecb_file)


class ECBFile(object):

    """An ECBFile is an intermediary object used by the ECBConverter. It is given
    the ECB and TTK directories, the topic identifier and the filename and then
    creates a TarsqiDocument for the ECB file. """

    def __init__(self, ecb_directory, ttk_directory, topic, fname):
        self.topic = topic
        self.ecb_file = os.path.join(ecb_directory, 'data', fname)
        self.ttk_file = os.path.join(ttk_directory, 'data', fname)
        self.tarsqidoc = _get_tarsqidoc_from_ecb_file(self.ecb_file)
        self.tarsqidoc.sourcedoc.filename = self.ecb_file
        # here we fake a pipeline for the metadata
        pipeline = [ProcessingStep(pipeline=[("ECB_CONVERTER", None)])]
        self.tarsqidoc.metadata['processing_steps'] = pipeline
        # and store the topic id since we do not to want to rely just on the
        # directory structure
        self.tarsqidoc.metadata['topic'] = topic

    def __str__(self):
        return "<ECBFile topic=%s %s>" % (self.topic, self.ecb_file)

    def write(self):
        path, fname = os.path.split(self.ttk_file)
        if not os.path.exists(path):
            os.makedirs(path)
        self.tarsqidoc.print_all(self.ttk_file)


### UTILITIES

def _makedir(directory):
    if os.path.exists(directory):
        exit("ERROR: directory already exists")
    else:
        os.makedirs(directory)


def _get_tarsqidoc(infile, source, metadata=True):
    """Return an instance of TarsqiDocument for infile"""
    opts = [("--source-format", source), ("--trap-errors", "False")]
    t = tarsqi.Tarsqi(opts, infile, None)
    t.source_parser.parse_file(t.input, t.tarsqidoc)
    t.metadata_parser.parse(t.tarsqidoc)
    return t.tarsqidoc


def _get_tarsqidoc_from_ecb_file(infile):
    """Return an instance of TarsqiDocument for infile. This is a special case of
    _get_tarsqidoc() for ECB files since those do not allow us to use a source
    parser in the regular way since ECB files are neither of the text type or
    the xml type."""
    opts = [("--source-format", "xml"), ("--trap-errors", "False")]
    t = tarsqi.Tarsqi(opts, infile, None)
    # create an XML string from the ECB file
    with codecs.open(t.input, encoding="utf8") as fh:
        content = "<text>%s</text>" % fh.read().replace('&', '&amp;')
    t.source_parser.parse_string(content, t.tarsqidoc)
    t.metadata_parser.parse(t.tarsqidoc)
    for mention in t.tarsqidoc.sourcedoc.tags.find_tags('MENTION'):
        # this is somewhat dangerous because we are not checking whether there
        # is a double quote in the string, but those do not happen to occur
        text = t.tarsqidoc.text(mention.begin, mention.end)
        mention.attrs["text"] = text
    return t.tarsqidoc


if __name__ == '__main__':

    long_options = ['timebank2ttk', 'thyme2ttk', 'ttk2html',
                    'knowtator2ttk', 'ttk2knowtator', 'ecb2ttk',
                    'tarsqi', 'show-links']
    (opts, args) = getopt.getopt(sys.argv[1:], 'i:o:', long_options)
    opts = { k: v for k, v in opts }
    limit = 10 if DEBUG else sys.maxsize

    if '--timebank2ttk' in opts:
        convert_timebank(args[0], args[1])

    elif '--thyme2ttk' in opts:
        convert_thyme(args[0], args[1], args[2], limit)

    elif '--knowtator2ttk' in opts:
        tarsqi_tags = True if '--tarsqi' in opts else False
        if os.path.isfile(args[0]):
            if os.path.exists(args[1]):
                exit("ERROR: output file already exists")
            converter = KnowtatorConverter(text_file=args[0], ttk_file=args[1])
            converter.convert(tarsqi_tags)
        elif os.path.isdir(args[0]):
            if os.path.exists(args[1]):
                exit("ERROR: output directory already exists")
            convert_knowtator(args[0], args[1], limit, tarsqi_tags)
        else:
            exit("ERROR: input is not a file or directory")

    elif '--ttk2html' in opts:
        limit = 10 if DEBUG else sys.maxsize
        showlinks = True if '--show-links' in opts else False
        if os.path.exists(args[1]):
            exit("ERROR: output '%s' already exists" % args[1])
        elif os.path.isdir(args[0]):
            convert_ttk_dir_into_html(args[0], args[1], showlinks, limit)
        elif os.path.isfile(args[0]):
            convert_ttk_file_into_html(args[0], args[1], showlinks)
        else:
            exit("ERROR: incorrect input")

    elif '--ttk2knowtator' in opts:
        convert_ttk_into_knowtator(args[0], args[1], args[2])

    elif '--ecb2ttk' in opts:
        indir = os.path.abspath(args[0])
        outdir = os.path.abspath(args[1])
        ECBConverter(indir, outdir).convert()


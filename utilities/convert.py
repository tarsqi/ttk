"""convert.py

Some format conversion utilities.

1. Convert LDC TimeBank into a modern TimeBank in the TTK format.

   $ python convert.py --timebank2ttk TIMEBANK_DIR TTK_DIR

   Converts TimeBank 1.2 as released by LDC into a version without makeinstance
   tags using the TTK format. This should be run on the data/extra files in the
   LDC distribution because those have the metadata that allow the TimeBank meta
   data parser to find the DCT.

2. Convert Thyme format into TTK.

   $ python convert.py --thyme2ttk THYME_TEXT_DIR THYME_ANNO_DIR TTK_DIR

   Note that in the Thyme corpus we have annotation directories like
   AnnotationData/coloncancer/Dev, whereas in the text directories we find
   TextData/dev. The latter will have more files than the former. Files in
   THYME_TEXT_DIR but not in THYME_ANNO_DIR will be ignored.

3. Convert the TTK format into HTML.

   $ python convert.py --ttk2html TTK_DIR HTML_DIR
   $ python convert.py --ttk2html --show-links TTK_DIR HTML_DIR

   Converts TTK files in TTK_DIR into HTML files in HTML_DIR, if --show-links is
   used links are shown in addition to the timexes and events.

4. Convert Knowtator format into TTK.

   $ python convert.py --knowtator2ttk KNOWTATOR_DIR TTK_DIR
   $ python convert.py --knowtator2ttk --tarsqi KNOWTATOR_DIR TTK_DIR

   This is not a general conversion from any Knowtator output, it assumes that
   the input annotations are all events. If the --tarsqi option is used then the
   event tags are put in the tarsqi_tags repository, by default they are put in
   the source_tags repository (that is, they are not considered Tarsqi results),
   using the --tarsqi option can be useful for evaluation.

"""

import os, sys, getopt, codecs
from xml.dom import minidom, Node

import path
import tarsqi
from docmodel.main import create_source_parser
from docmodel.main import create_metadata_parser
from docmodel.main import create_docstructure_parser
from docmodel.document import TarsqiDocument, Tag
from library.main import TarsqiLibrary

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
            print fname
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

def convert_thyme(thyme_text_dir, thyme_anno_dir, out_dir, limit=sys.maxint):
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
            print fname
            thyme_anno_file = os.path.join(thyme_anno_dir, fname, timeml_files[0])
            _convert_thyme_file(thyme_text_file, thyme_anno_file, out_file)


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
            if timex_idx.has_key(timex.id):
                print "WARNING: timex %s already exists" % timex.id
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
            tarsqidoc.tags.add_tag('TIMEX3', begin, end, attrs)
        except ValueError:
            print "Skipping discontinuous timex"


def _add_events_to_tarsqidoc(events, event_idx, dct, tarsqidoc):
    """Add an event from the Thyme file. Also includes adding a TLINK to the DCT,
    for this link we generate a new link identifier."""
    dct_rel_id = 0
    for event in events:
        try:
            begin, end = event.span.split(',')
            if event_idx.has_key(event.id):
                print "WARNING: event %s already exists" % event.id
            event_idx[event.id] = begin
            # TODO: is it okay for these to be the same?
            attrs = { EID: event.id, EIID: event.id}
            tarsqidoc.tags.add_tag('EVENT', begin, end, attrs)
            dct_rel_id += 1
            attrs = { LID: LinkID.next(),
                      RELTYPE: event.DocTimeRel,
                      EVENT_INSTANCE_ID: event.id,
                      RELATED_TO_TIME: dct.id }
            tarsqidoc.tags.add_tag('TLINK', None, None, attrs)
        except ValueError:
            print "Skipping discontinuous event"


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
        tarsqidoc.tags.add_tag(rel.type, None, None, attrs)


def _source_attr_name(link_type, source_id, timex_idx, event_idx):
    if link_type == ALINK:
        return EVENT_INSTANCE_ID
    elif source_id in timex_idx:
        return TIME_ID
    elif source_id in event_idx:
        return EVENT_INSTANCE_ID
    else:
        print "WARNING: cannot find attribute name for", source_id


def _target_attr_name(link_type, target_id, timex_idx, event_idx):
    if link_type == ALINK:
        return RELATED_TO_EVENT_INSTANCE
    elif target_id in timex_idx:
        return RELATED_TO_TIME
    elif target_id in event_idx:
        return RELATED_TO_EVENT_INSTANCE
    else:
        print "WARNING: cannot find attribute name for", target_id


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

def convert_knowtator(knowtator_dir, ttk_dir, limit, tarsqi_tags=False):
    """Convert pairs of Knowtator files (source plus annotations) with event
    information into single TTK files. This assumes that the information needed
    is in annotation and classMention tags and that all those tags have event
    information. The event tags are added to the source tags, not to the tarsqi
    tags, but if tarsqi_tags option is True then they will be added to the
    tarsqi tags repository"""
    knowtator_dir = os.path.abspath(knowtator_dir)
    ttk_dir = os.path.abspath(ttk_dir)
    _makedir(ttk_dir)
    count = 0
    fnames = _read_knowtator_filenames(knowtator_dir)
    for fname in fnames:
        count += 1
        if count > limit:
            break
        print fname
        source_file = os.path.join(knowtator_dir, fname)
        anno_file = os.path.join(knowtator_dir, fname + '.knowtator.xml')
        # this assumes the .txt extension and replaces it with .ttk
        ttk_fname = fname[:-3] + 'ttk'
        ttk_file = os.path.join(ttk_dir, ttk_fname)
        _convert_knowtator_file(source_file, anno_file, ttk_file, tarsqi_tags)


def _read_knowtator_filenames(knowtator_dir):
    """Read the list of file names. Note that with Knowtator we have a separate
    annotation file in addition to the source file: for each source file named
    'file.txt' we also have an annotations file named 'file.txt.knowtator.xml'."""
    fnames = os.listdir(knowtator_dir)
    return [f for f in fnames if not f.endswith('knowtator.xml')]


def _convert_knowtator_file(source_file, anno_file, ttk_file, tarsqi_tags):
    dom = minidom.parse(anno_file)
    annotations = dom.getElementsByTagName('annotation')
    class_mentions = dom.getElementsByTagName('classMention')
    events = {}
    for ann in annotations:
        mention_id = ann.getElementsByTagName('mention')[0].getAttribute('id')
        start = ann.getElementsByTagName('span')[0].getAttribute('start')
        end = ann.getElementsByTagName('span')[0].getAttribute('end')
        events[mention_id] = { 'start': start, 'end': end }
    for cm in class_mentions:
        cm_id = cm.getAttribute('id')
        mention_class = cm.getElementsByTagName('mentionClass')[0]
        class_name = mention_class.firstChild.data
        events[cm_id]['class'] = class_name
    tarsqidoc = _get_tarsqidoc(source_file, "text")
    tags = []
    for event_id, event in events.items():
        tag = _create_event_tag(event_id, event)
        if tarsqi_tags:
            tarsqidoc.tags.append(tag)
        else:
            tarsqidoc.sourcedoc.tags.append(tag)
    tarsqidoc.print_all(ttk_file)


def _create_event_tag(event_id, event):
    feats = { 'class': event['class'],
              'eid': 'e' + event_id,
              'eiid': 'ei' + event_id }
    return Tag('EVENT', event['start'], event['end'], feats)


### CONVERTING TTK INTO HTML

def convert_ttk_dir_into_html(ttk_dir, html_dir, showlinks, limit):
    ttk_dir = os.path.abspath(ttk_dir)
    html_dir = os.path.abspath(html_dir)
    _makedir(html_dir)
    print ttk_dir
    print html_dir
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
    print "creating", html_file
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
    for elist in event_idx['open'].values() + timex_idx['open'].values():
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
        if source is None: print "WARNING, no source for", link
        if target is None: print "WARNING, no target for", link
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
        print "WARNING", (link_id, source_id, reltype, target_id)


### UTILITIES

def _makedir(directory):
    if os.path.exists(directory):
        exit("ERROR: directory already exists")
    else:
        os.makedirs(directory)


def _get_tarsqidoc(infile, source, metadata=True):
    """Return an instance of TarsqiDocument for infile"""
    opts = [("--source", source), ("--trap-errors", "False")]
    t = tarsqi.Tarsqi(opts, infile, None)
    t.source_parser.parse_file(t.input, t.tarsqidoc)
    t.metadata_parser.parse(t.tarsqidoc)
    return t.tarsqidoc


if __name__ == '__main__':

    long_options = ['timebank2ttk', 'thyme2ttk', 'ttk2html',
                    'knowtator2ttk', 'tarsqi', 'show-links']
    (opts, args) = getopt.getopt(sys.argv[1:], 'i:o:', long_options)
    opts = { k: v for k, v in opts }
    limit = 10 if DEBUG else sys.maxint
    if '--timebank2ttk' in opts:
        convert_timebank(args[0], args[1])
    elif '--thyme2ttk' in opts:
        convert_thyme(args[0], args[1], args[2], limit)
    elif '--knowtator2ttk' in opts:
        tarsqi_tags = True if '--tarsqi' in opts else False
        convert_knowtator(args[0], args[1], limit, tarsqi_tags)
    elif '--ttk2html' in opts:
        limit = 10 if DEBUG else sys.maxint
        showlinks = True if '--show-links' in opts else False
        if os.path.exists(args[1]):
            exit("ERROR: output '%s' already exists" % args[1])
        elif os.path.isdir(args[0]):
            convert_ttk_dir_into_html(args[0], args[1], showlinks, limit)
        elif os.path.isfile(args[0]):
            convert_ttk_file_into_html(args[0], args[1], showlinks)
        else:
            exit("ERROR: incorrect input")

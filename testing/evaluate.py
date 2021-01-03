"""evaluate.py

Script to create a system response for a given gold standard and then compare
the system response to that gold standard.

USAGE:

   $ python evaluate.py --run --gold DIR1 --system DIR2 [OPTIONS]
   $ python evaluate.py --comp --gold DIR1 --system DIR2 [OPTIONS]
   $ python evaluate.py --diff --gold DIR1 --system DIR2 --out DIR3 [OPTIONS]

In the first invocation, the script takes the gold standard files in DIR1 and
for each file creates a system file in DIR2 that does not have the gold standard
tags but the tags generated by the system. In the second invocation, the script
compares the system results to the gold standard and writes precision, recall
and f-score results to the standard output. In the third invocation, html files
showing the difference between files will be written to DIR3.

All files in the gold standard are expected to be TTK files. See the code in
utilities.convert for how to convert to the TTK format.

OPTIONS:

   --limit INT

      Caps the number of files processed from the directory. If no limit is
      given all files will be processed.

   --display=CHOICE1,CHOICE2,...

      This determines what entities pairs are displayed. By default all entity
      pairs from the gold and system tags are displayed: matches, partial
      matches, false positives and false negatives. But if the --display option
      is used then only the ones listed are displayed. Available choices are:
      EXACT_MATCH, PARTIAL_MATCH, NO_MATCH_FP and NO_MATCH_FN. This option is
      only relevant for the third invocation above. Example:

         --display=PARTIAL_MATCH,NO_MATCH_FN

      With this value only partial matches and false negatives are displayed.

"""

import os, sys, shutil, copy, getopt, StringIO

sys.path.insert(0, '..')
sys.path.insert(0, '.')

from __future__ import division

import tarsqi
from library.main import LIBRARY


# Keep the directory this script was called from for later use (Tarsqi will
# change current directories while processing), also keep the directory of this
# script around.
EXEC_DIR = os.getcwd()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


EVENT = LIBRARY.timeml.EVENT
TIMEX = LIBRARY.timeml.TIMEX
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK

LINK_TAGS = (ALINK, SLINK, TLINK)
TIMEML_TAGS = (EVENT, TIMEX, ALINK, SLINK, TLINK)

TID = LIBRARY.timeml.TID
EIID = LIBRARY.timeml.EIID

RELTYPE = LIBRARY.timeml.RELTYPE
TIME_ID = LIBRARY.timeml.TIME_ID
EVENT_INSTANCE_ID = LIBRARY.timeml.EVENT_INSTANCE_ID
RELATED_TO_TIME = LIBRARY.timeml.RELATED_TO_TIME
RELATED_TO_EVENT_INSTANCE = LIBRARY.timeml.RELATED_TO_EVENT_INSTANCE
SUBORDINATED_EVENT_INSTANCE = LIBRARY.timeml.SUBORDINATED_EVENT_INSTANCE


# the four kinds of aligned entities
EXACT_MATCH = 'EXACT_MATCH'
PARTIAL_MATCH = 'PARTIAL_MATCH'
NO_MATCH_FP = 'NO_MATCH_FP'
NO_MATCH_FN = 'NO_MATCH_FN'
DISPLAY_CHOICES = [EXACT_MATCH, PARTIAL_MATCH, NO_MATCH_FP, NO_MATCH_FN]


# style file used for the html display of differences
CSS = """
<style>
div { display: block }
p { margin: 5pt; margin-bottom: 15pt; padding: 5pt; }
table { margin-bottom: 25px; width: 100%; }
table.scores { margin: 10px; margin-bottom: 25px; width: auto; }
.bordered { border: thin dotted black; }
sup.s { color: darkred; font-weight: bold; }
sup.chunk { color: darkblue; font-weight: bold; }
sup.pos { color: darkblue; font-weight: bold; }
sup.lex { color: darkgreen; font-weight: bold; font-size: 60%; }
.bracket { color: darkblue; font-weight: bold; }
.sbracket { color: darkred; font-weight: bold; }
entity { color: darkred; text-decoration: underline; }")
</style>
"""


def create_system_files_from_gold_standard(gold_dir, system_dir, limit):
    """Take the TTK files in gold_dir and create TTK files in system_dir that have
    the same text and docelement tags, do not have the other tarsqi tags from
    the gold standard and have tags as added by the current system."""
    print system_dir
    if os.path.exists(system_dir):
        exit("Error: directory %s already exists" % system_dir)
    else:
        os.makedirs(system_dir)
    # get the absolute paths now because components may change the current directory
    gold_dir = os.path.abspath(gold_dir)
    system_dir = os.path.abspath(system_dir)
    count = 0
    for fname in os.listdir(gold_dir):
        count += 1
        if count > limit:
            break
        print fname
        gold_file = os.path.join(gold_dir, fname)
        system_file = os.path.join(system_dir, fname)
        create_system_file_from_gold_standard(gold_file, system_file)


def create_system_file_from_gold_standard(gold_file, system_file):
    """Take gold_file, a TTK file, and create the TTK file system_file that has
    the same text and docelement tags, does not have the other tarsqi tags from
    the gold standard and has tags as added by the current system."""
    # TODO: need to deal with the fact that with THYME we have a ttk version and
    # we use source=ttk, but there really needs to be a metadata parser that
    # does works for THYME documents. One option is to have the conversion find
    # the DCT.
    tarsqi_inst, tarsqidoc = tarsqi.load_ttk_document(gold_file)
    # before you reset, keep the docelement tags so that we do not have to rerun
    # the document parser
    docelement_tags = [t for t in tarsqidoc.tags.all_tags() if t.name == 'docelement']
    tarsqidoc.tags.reset()
    for tag in docelement_tags:
        tarsqidoc.tags.append(tag)
    tarsqidoc.tags.index()
    for (name, wrapper) in tarsqi_inst.pipeline:
        tarsqi_inst._apply_component(name, wrapper, tarsqidoc)
    tarsqidoc.print_all(system_file)


def compare_dirs(gold_dir, system_dir, limit=sys.maxint):
    """Generate the precision, recall and f-score numbers for the directories."""
    fstats = []
    fnames = _collect_files(gold_dir, system_dir, limit)
    for fname in fnames:
        print fname
        fstats.append(
            FileStatistics(os.path.join(gold_dir, fname),
                           os.path.join(system_dir, fname)))
    dstats = DirectoryStatistics(system_dir, fstats)
    dstats.pp()


def view_differences(gold_dir, system_dir, display_dir, display_choices,
                     limit=sys.maxint):
    """Create HTML files that view the differences."""
    display_dir = _create_display_dir(display_dir)
    fnames = _collect_files(gold_dir, system_dir, limit)
    for fname in fnames:
        print fname
        FileStatistics(os.path.join(gold_dir, fname),
                       os.path.join(system_dir, fname),
                       display_dir, display_choices)


def _collect_files(gold_dir, system_dir, limit):
    """Return the list of files to run the comparison on."""
    gold_files = os.listdir(gold_dir)
    system_files = os.listdir(system_dir)
    # don't assume the directory content is the same, take the intersection
    fnames = sorted(list(set(gold_files).intersection(set(system_files))))
    # TODO: includes a hack to avoid a file, get rid of it
    fnames = [f for f in fnames[:limit] if not f.endswith('wsj_0907.tml')]
    return fnames


def _create_display_dir(display_dir):
    """Create the display directory and initialize it with the icons needed for
    the display."""
    if display_dir is not None:
        if not os.path.isabs(display_dir):
            display_dir = os.path.abspath(os.path.join(EXEC_DIR, display_dir))
            if os.path.exists(display_dir):
                exit("ERROR: directory '%s' already exists" % display_dir)
            else:
                # setup the output directory
                os.makedirs(display_dir)
                os.makedirs(os.path.join(display_dir, 'icons'))
                icons = ('check-green.png', 'check-orange.png', 'cross-red.png')
                for icon in icons:
                    shutil.copyfile(os.path.join(SCRIPT_DIR, 'icons', icon),
                                    os.path.join(display_dir, 'icons', icon))
    return display_dir


def _get_annotations(tag_repository):
    """Return a dictionary of the TimeML annotations in the tag repository."""
    # TODO: is there solid motivation to use this instead of TagRepository
    # itself?
    timeml_tags = (EVENT, TIMEX, ALINK, SLINK, TLINK)
    annotations = { tagname: {} for tagname in timeml_tags }
    event_idx = {}
    timex_idx = {}
    for tag in tag_repository.all_tags():
        if tag.name == EVENT:
            event_idx[tag.attrs[EIID]] = tag
        elif tag.name == TIMEX:
            timex_idx[tag.attrs[TID]] = tag
    for tag in tag_repository.all_tags():
        if tag.name in timeml_tags:
            offsets = _get_offsets(tag, event_idx, timex_idx)
            if offsets is not None:
                annotations[tag.name][offsets] = tag.attrs
    return annotations


def _get_offsets(tag, event_idx, timex_idx):
    """Get begin and end offsets for the tag. For an event or time, this is a pair
    of offsets, for example (13,16). For a link, this is pair of the offsets of
    the source and target of the link, for example ((13,16),(24,29))."""
    if tag.name in LINK_TAGS:
        id1, id1_type = tag.attrs.get(TIME_ID), TIMEX
        if id1 is None:
            saved = "%s-%s" % (id1, id1_type)
            id1, id1_type = tag.attrs.get(EVENT_INSTANCE_ID), EVENT
        id2, id2_type = tag.attrs.get(RELATED_TO_TIME), TIMEX
        if id2 is None:
            id2, id2_type = tag.attrs.get(RELATED_TO_EVENT_INSTANCE), EVENT
        if id2 is None:
            id2, id2_type = tag.attrs.get(SUBORDINATED_EVENT_INSTANCE), EVENT
        offsets = [_retrieve_from_index(id1, id1_type, event_idx, timex_idx),
                   _retrieve_from_index(id2, id2_type, event_idx, timex_idx)]
        if len(offsets) != 2:
            _offset_warning("unexpected offsets", tag, offsets)
            return None
        elif offsets[0][0] is None or offsets[1][0] is None:
            _offset_warning("cannot find source and/or target", tag, offsets)
            return None
        else:
            return tuple(offsets)
    else:
        return (tag.begin, tag.end)


def _retrieve_from_index(identifier, tagtype, event_idx, timex_idx):
    idx = event_idx if tagtype == EVENT else timex_idx
    try:
        return (idx[identifier].begin, idx[identifier].end)
    except KeyError:
        return (None, None)


def precision(tp, fp):
    try:
        return (tp / (tp + fp))
    except ZeroDivisionError:
        return None


def recall(tp, fn):
    try:
        return tp / (tp + fn)
    except ZeroDivisionError:
        return None


def fscore(tp, fp, fn):
    p = precision(tp, fp)
    r = recall(tp, fn)
    if p is None or r is None:
        return None
    try:
        return (2 * p * r) / (p + r)
    except ZeroDivisionError:
        return None


def _as_float_string(f):
    """Takes a floating point number and returns it as a formatted string"""
    return "%.2f" % f if f is not None else 'nil'


def _offset_warning(message, tag, offsets):
    print "WARNING: %s" % message
    print "         %s" % offsets
    print "         %s" % tag.as_ttk_tag()


def print_annotations(annotations, tag=None):
    for tagname in sorted(annotations):
        if tag is not None and tag != tagname:
            continue
        print "\n", tagname
        for offsets in sorted(annotations[tagname]):
            attrs = annotations[tagname][offsets].items()
            attrs_str = ' '.join(["%s=%s" % (a,v) for a,v in attrs])
            print "  %s %s" % (offsets, attrs_str)


class FileStatistics(object):

    def __init__(self, gold_file, system_file,
                 display_dir=None, display_choices=None):
        tarsqi_instance, tarsqi_doc = tarsqi.load_ttk_document(gold_file)
        self.tarsqidoc_gold = tarsqi_doc
        tarsqi_instance, tarsqi_doc = tarsqi.load_ttk_document(system_file)
        self.tarsqidoc_system = tarsqi_doc
        self.filename = system_file
        self.gold = _get_annotations(self.tarsqidoc_gold.tags)
        self.system = _get_annotations(self.tarsqidoc_system.tags)
        self.events = EntityStatistics(self, EVENT, display_dir, display_choices)
        self.timexes = EntityStatistics(self, TIMEX, display_dir, display_choices)
        self.alinks = LinkStatistics(self.filename, ALINK, self.gold, self.system)
        self.slinks = LinkStatistics(self.filename, SLINK, self.gold, self.system)
        self.tlinks = LinkStatistics(self.filename, TLINK, self.gold, self.system)

    def __str__(self):
        return "%s\n%s\n%s\n%s\n%s" % (self.events, self.timexes,
                                       self.alinks, self.slinks, self.tlinks)


class DirectoryStatistics(FileStatistics):

    def __init__(self, directory, statslist):
        self.filename = directory
        self.statistics = statslist
        self.events = AggregateEntityStatistics(directory, [s.events for s in statslist])
        self.timexes = AggregateEntityStatistics(directory, [s.timexes for s in statslist])
        self.alinks = AggregateLinkStatistics(directory, [s.alinks for s in statslist])
        self.slinks = AggregateLinkStatistics(directory, [s.slinks for s in statslist])
        self.tlinks = AggregateLinkStatistics(directory, [s.tlinks for s in statslist])

    def __str__(self):
        return "%s\n%s\n%s\n%s\n%s" % (
            self.events, self.timexes, self.alinks, self.slinks, self.tlinks)

    def pp(self):
        print "\n%s\n" % self


class EntityStatistics(object):

    def __init__(self, file_statistics, tagname, display_dir, display_choices):
        self.filename = file_statistics.filename
        self.tagname = tagname
        self.tarsqidoc_gold = file_statistics.tarsqidoc_gold
        self.tarsqidoc_system = file_statistics.tarsqidoc_system
        self.gold_tags = file_statistics.gold[self.tagname]
        self.system_tags = file_statistics.system[self.tagname]
        self.tp = 0
        self.fp = 0
        self.fn = 0
        self._collect_counts()
        # the following code presents the differences between the gold and the
        # system, the underlying counting should probably be used for the P&R as
        # well (allowing strict versus relaxed matching, whereas the above only
        # has strict matching).
        if display_dir is not None:
            Viewer(self, display_dir, display_choices)

    def __str__(self):
        return "<Statistics %s %s tp:%s fp:%s fn:%s precision=%s recall=%s f-score=%s>" % \
            (self.tagname, self.filename, self.tp, self.fp, self.fn,
             _as_float_string(self.precision()),
             _as_float_string(self.recall()),
             _as_float_string(self.fscore()))

    def precision(self):
        return precision(self.tp, self.fp)

    def recall(self):
        return recall(self.tp, self.fn)

    def fscore(self):
        return fscore(self.tp, self.fp, self.fn)

    def _collect_counts(self):
        """Collect the counts for true positives, false positives and false
        negatives."""
        # TODO. This does not take the full-range into account and therefore
        # gives much lower numbers for cases where multi-token events were
        # imported. It also does not allow for relaxed matching.
        for t in self.system_tags.keys():
            if t in self.gold_tags:
                self.tp += 1
            else:
                self.fp += 1
        for t in self.gold_tags.keys():
            if t not in self.system_tags:
                self.fn += 1


class LinkStatistics(object):

    def __init__(self, filename, tagname, gold_annotations, system_annotations):
        self.filename = filename
        self.tagname = tagname
        self.gold_tags = gold_annotations[tagname]
        self.system_tags = system_annotations[tagname]
        self.overlap = self._overlap(self.gold_tags, self.system_tags)
        self.correct = 0
        self.incorrect = 0
        for offset in self.overlap:
            if self.gold_tags[offset][RELTYPE] == self.system_tags[offset][RELTYPE]:
                self.correct += 1
            else:
                self.incorrect += 1

    def __str__(self):
        accuracy = self.accuracy()
        astring = "nil" if accuracy is None else "%.2f" % accuracy
        return "<Statistics %s %s correct:%s incorrect:%s accuracy:%s>" % \
            (self.tagname, self.filename, self.correct, self.incorrect, astring)

    @staticmethod
    def _overlap(annotations1, annotations2):
        """Now just gets the keys that both have in common, should include links where
        source and target are reversed."""
        return [val for val in annotations1 if val in annotations2]

    def accuracy(self):
        try:
            return self.correct / (self.correct + self.incorrect)
        except ZeroDivisionError:
            return None


class AggregateEntityStatistics(EntityStatistics):

    def __init__(self, directory, statistics_list):
        self.tagname = statistics_list[0].tagname
        self.filename = directory
        self.statistics = statistics_list
        self.tp = sum([stats.tp for stats in statistics_list])
        self.fp = sum([stats.fp for stats in statistics_list])
        self.fn = sum([stats.fn for stats in statistics_list])


class AggregateLinkStatistics(LinkStatistics):

    def __init__(self, directory, statistics_list):
        self.tagname = statistics_list[0].tagname
        self.filename = directory
        self.statistics = statistics_list
        self.correct = sum([stats.correct for stats in statistics_list])
        self.incorrect = sum([stats.incorrect for stats in statistics_list])


class Viewer(object):

    """Creates the HTML files that show the differences between the entities in
    two files."""

    def __init__(self, entity_statistics, display_dir, display_choices):
        """Take the data from the EntityStatistics instance (which got most of those
        from the FileStatistics instance)."""
        self.entity_stats = entity_statistics
        self.filename = entity_statistics.filename
        self.tagname = entity_statistics.tagname
        self.tarsqidoc_gold = entity_statistics.tarsqidoc_gold
        self.tarsqidoc_system = entity_statistics.tarsqidoc_system
        self.gold_tags = entity_statistics.gold_tags
        self.system_tags = entity_statistics.system_tags
        self.display_dir = display_dir
        self.display_choices = display_choices
        self._build_idxs()
        self._align_tags()
        self._display_aligned_tags()

    def _build_idxs(self):
        """Builds indexes that store the begin and end offset of s, ng and vg
        tags. In addition, it stores the end offset of a lex tag and the lex
        tag's associated pos."""
        self.open_idx = { 's': set(), 'ng': set(), 'vg': set() }
        self.close_idx = { 's': set(), 'ng': set(), 'vg': set(), 'lex': {} }
        s_tags = self.tarsqidoc_system.tags.find_tags('s')
        vg_tags = self.tarsqidoc_system.tags.find_tags('vg')
        ng_tags = self.tarsqidoc_system.tags.find_tags('ng')
        lex_tags = self.tarsqidoc_system.tags.find_tags('lex')
        open_idx = { 's': set(), 'ng': set(), 'vg': set() }
        close_idx = { 's': set(), 'ng': set(), 'vg': set(), 'lex': {} }
        self._update_idxs(s_tags, 's')
        self._update_idxs(ng_tags, 'ng')
        self._update_idxs(vg_tags, 'vg')
        for lex in lex_tags:
            self.close_idx['lex'][lex.end] = lex.attrs['pos']

    def _update_idxs(self, tags, tagname):
        for t in tags:
            self.open_idx[tagname].add(t.begin)
            self.close_idx[tagname].add(t.end)

    def _align_tags(self):
        """Takes two lists of annotations ordered on text position and returns
        them as lists of paired up annotations. Annotations will only pair up if
        they overlap, if a gold or system annotation does not overlap with a
        counterpart on the other side then it will be in a pair with None."""
        gold = [EntityAnnotation(k, v) for k, v in self.gold_tags.items()]
        system = [EntityAnnotation(k, v) for k, v in self.system_tags.items()]
        # Removing duplicates also sorts the annotations
        gold = self._remove_duplicates(gold)
        system = self._remove_duplicates(system)
        self.alignments = []
        while gold or system:
            if not gold:
                self.alignments.append(Alignment(self, None, system.pop(0)))
            elif not system:
                self.alignments.append(Alignment(self, gold.pop(0), None))
            elif gold[0].overlaps_with(system[0]):
                self.alignments.append(Alignment(self, gold.pop(0), system.pop(0)))
            elif gold[0].end < system[0].begin:
                self.alignments.append(Alignment(self, gold.pop(0), None))
            elif gold[0].begin > system[0].end:
                self.alignments.append(Alignment(self, None, system.pop(0)))
            else:
                exit("ERROR: no option available, infinite loop starting...")

    @staticmethod
    def _remove_duplicates(annotations):
        """This is to remove duplicates from the annotations. The reason why
        this was put in is that with tag import there are cases when an imported
        tag spans two chunks and it will be imported into each chunk. This needs
        to be fixed in the tag import of course, but in th emean time we do not
        want it dilute results here. The result is sorted on text position."""
        tmp = {}
        for annotation in sorted(annotations):
            tmp[annotation.offsets()] = annotation
        return sorted(tmp.values())

    def _display_aligned_tags(self):
        # NOTE: when we run this we are in the ttk directory, even though we
        # started in the testing subdirectory, adjust paths as needed
        fname = os.path.join(self.display_dir, os.path.basename(self.filename))
        fh = open("%s.%s.html" % (fname, self.tagname), 'w')
        fh.write("<html>\n<head>%s</head>\n\n" % CSS)
        fh.write("<body class=scores>\n\n")
        fh.write("<h2>Precision and recall on this file</h2>\n\n")
        self._display_p_and_r(fh)
        fh.write("<h2>Aligning the key and response %s tags</h2>\n\n" % self.tagname)
        self._display_legend(fh)
        for alignment in self.alignments:
            if self.display_choices[alignment.status]:
                alignment.html(fh)
        fh.write("</body>\n</html>\n")

    def _display_p_and_r(self, fh):
        stats = self.entity_stats
        # P&R as calculated on the EntityStatistics
        p1, r1, f1 = stats.precision(), stats.recall(), stats.fscore()
        # P&R as calculated here, which uses the alignments array which takes
        # into account the full-range attribute, so it gets much higher results
        # for cases when we impoerted tags.
        tp, fp, fn = self._count_matches(strict=True)
        p2, r2, f2 = precision(tp, fp), recall(tp, fn), fscore(tp, fp, fn)
        tp, fp, fn = self._count_matches(strict=False)
        p3, r3, f3 = precision(tp, fp), recall(tp, fn), fscore(tp, fp, fn)
        self._p_and_r_table(fh, ('strict', 'relaxed'), (p2, p3), (r2, r3), (f2, f3))

    def _count_matches(self, strict=True):
        tp, fp, fn = 0, 0, 0
        for alignment in self.alignments:
            if alignment.status == NO_MATCH_FP:
                fp += 1
            elif alignment.status == NO_MATCH_FN:
                fn += 1
            elif alignment.status == PARTIAL_MATCH:
                if strict:
                    fp += 1
                    fn += 1
                else:
                    tp += 1
            elif alignment.status == EXACT_MATCH:
                tp += 1
        return (tp, fp, fn)

    def _p_and_r_table(self, fh, headers, p_scores, r_scores, f_scores):
        fh.write("<table class=scores cellpadding=8 cellspacing=0 border=1>\n")
        nbsp, p_str, r_str, f_str = '&nbsp;', 'precision', 'recall', 'f-score'
        HTML.row(fh, [nbsp] + list(headers))
        HTML.row(fh, [p_str] + [ _as_float_string(p) for p in p_scores])
        HTML.row(fh, [r_str] + [ _as_float_string(r) for r in r_scores])
        HTML.row(fh, [f_str] + [ _as_float_string(f) for f in f_scores])
        fh.write("</table>\n\n")

    def _display_legend(self, fh):
        def img(src): return '<img src="icons/%s.png" height=20>' % src
        fh.write("<table class=scores cellpadding=8 cellspacing=0 border=1>\n")
        em = len([a for a in self.alignments if a.status == EXACT_MATCH])
        pm = len([a for a in self.alignments if a.status == PARTIAL_MATCH])
        fp = len([a for a in self.alignments if a.status == NO_MATCH_FP])
        fn = len([a for a in self.alignments if a.status == NO_MATCH_FN])
        HTML.row(fh, [img("check-green"), 'exact match', em])
        HTML.row(fh, [img("check-orange"), 'partial match', pm])
        HTML.row(fh, [img('cross-red') + 'p',
                      'mismatch, false positive (precision error)', fp])
        HTML.row(fh, [img('cross-red') + 'r',
                      'mismatch, false negative (recall error)', fn])
        fh.write("</table>\n")
        icons = { EXACT_MATCH: img('check-green'),
                  PARTIAL_MATCH: img('check-orange'),
                  NO_MATCH_FP: img('cross-red') + 'p',
                  NO_MATCH_FN: img('cross-red') + 'r' }
        showing = [icons[choice]
                   for choice in DISPLAY_CHOICES
                   if self.display_choices[choice] is True]
        fh.write("<p class=bordered>Showing:&nbsp;&nbsp;%s</p>\n"
                 % '&nbsp;&nbsp;'.join(showing))


class EntityAnnotation(object):

    """Simple interface for an entity annotation."""

    def __init__(self, offsets, attrs):
        self.begin = offsets[0]
        self.end = offsets[1]
        # we keep these around so we can use them for sorting
        self.begin_head = self.begin
        self.end_head = self.end
        self.attrs = attrs
        full_range = self.attrs.get('full-range')
        if full_range is not None:
            begin, end = full_range.split('-')
            self.begin = int(begin)
            self.end = int(end)
        self.tarsqidoc = None  # filled in later by the Alignment instance

    def __str__(self):
        return "<EntityAnnotation %s:%s %s>" % (self.begin, self.end, self.attrs)

    def __eq__(self, other):
        return (self.begin == other.begin) \
            and (self.end == other.end) \
            and (self.begin_head == other.begin_head)

    def __ne__(self, other):
        return (self.begin != other.begin) \
            or (self.end != other.end) \
            or (self.begin_head != other.begin_head)

    def __lt__(self, other):
        return self._compare(other) < 0

    def __le__(self, other):
        return self._compare(other) <= 0

    def __gt__(self, other):
        return self._compare(other) > 0

    def __ge__(self, other):
        return self._compare(other) >= 0

    def _compare(self, other):
        # TODO: revisit this later, it is Python3 compliant, but that's about
        # the best you can say
        def comp(x, y):
            return (x > y) - (x < y)
        begin_comp = comp(self.begin, other.begin)
        if begin_comp != 0:
            return begin_comp
        end_comp = comp(self.end, other.end)
        if end_comp != 0:
            return end_comp
        return comp(self.begin_head, other.begin_head)

    def overlaps_with(self, other):
        return not (self.end <= other.begin or other.end <= self.begin)

    def has_same_span(self, other):
        return self.begin == other.begin and self.end == other.end

    def offsets(self):
        return (self.begin, self.end)


class Alignment(object):

    def __init__(self, entitystats, gold_annotation, system_annotation):
        self.tarsqidoc_gold = entitystats.tarsqidoc_gold
        self.tarsqidoc_system = entitystats.tarsqidoc_system
        self.gold_annotation = gold_annotation
        self.system_annotation = system_annotation
        self.open_idx = entitystats.open_idx
        self.close_idx = entitystats.close_idx
        if gold_annotation is not None:
            self.gold_annotation.tarsqidoc = self.tarsqidoc_gold
        if system_annotation is not None:
            self.system_annotation.tarsqidoc = self.tarsqidoc_system
        if self.gold_annotation is None:
            self.status = NO_MATCH_FP
        elif self.system_annotation is None:
            self.status = NO_MATCH_FN
        elif self.gold_annotation.has_same_span(self.system_annotation):
            self.status = EXACT_MATCH
        else:
            self.status = PARTIAL_MATCH

    def html(self, fh):
        def oneliner(text):
            return ' '.join(text.strip().split())
        image = self._get_status_image()
        p1, p2, text_span = self._get_span()
        span1 = self._get_span_with_entity(p1, text_span, self.gold_annotation)
        span2 = self._get_span_with_entity(p1, text_span, self.system_annotation)
        text = text_span.replace("\n", "<br/>")
        tagged_fragment = self._get_tagged_fragment(p1, p2, text_span)
        fh.write("<table cellpadding=5 cellspacing=4>\n\n")
        fh.write("<tr>\n")
        fh.write("  <td valign=top width=40>%s</td>\n" % image)
        fh.write("  <td class=bordered>\n")
        fh.write("     <span class=entity_span><i>%s:%s</i></span><br/>\n" % (p1, p2))
        fh.write("     <span class=entity_span>%s</span><br/>\n" % oneliner(span1))
        fh.write("     <span class=entity_span>%s</span>\n" % oneliner(span2))
        fh.write("  </td>\n")
        fh.write("</tr>\n\n")
        fh.write("<tr>\n")
        fh.write("  <td valign=top>&nbsp;</td>\n")
        fh.write("  <td class=bordered>%s</td>\n" % text)
        fh.write("</tr>\n\n")
        fh.write("<tr>\n")
        fh.write("  <td valign=top>&nbsp;</td>\n")
        fh.write("  <td class=bordered>%s</td>\n" % tagged_fragment)
        fh.write("</tr>\n\n")
        fh.write("</table>\n\n")

    def _get_status_image(self):
        if self.status == EXACT_MATCH:
            return '<img src="icons/check-green.png" height=20>'
        elif self.status == PARTIAL_MATCH:
            return '<img src="icons/check-orange.png" height=20>'
        elif self.status == NO_MATCH_FP:
            return '<img src="icons/cross-red.png" height=20>p'
        elif self.status == NO_MATCH_FN:
            return '<img src="icons/cross-red.png" height=20>r'

    def _get_span(self):
        offsets = []
        for annotation in self.gold_annotation, self.system_annotation:
            if annotation is not None:
                offsets.extend([annotation.begin, annotation.end])
        offsets.sort()
        span_begin = offsets[0] - 50
        span_end =  offsets[-1] + 50
        if span_begin < 0:
            span_begin = 0
        if span_end > len(self.tarsqidoc_gold.sourcedoc.text):
            span_end = len(self.tarsqidoc_gold.sourcedoc.text) -1
        return (span_begin, span_end,
                self.tarsqidoc_gold.sourcedoc[span_begin:span_end])

    def _get_span_with_entity(self, p1, text_span, annotation):
        if annotation is None:
            return text_span
        else:
            a1 = annotation.begin - p1
            a2 = annotation.end - p1
            return "%s<entity>%s</entity>%s" \
                % (text_span[:a1], text_span[a1:a2], text_span[a2:])

    def _get_tagged_fragment(self, p1, p2, text):
        def tag(cl, text): return "<sup class=%s>%s</sup>" % (cl, text)
        def brc(cl, bracket): return "<span class=%s>%s</span>" % (cl, bracket)
        output = StringIO.StringIO()
        for i in range(0, p2-p1):
            i_adjusted = i + p1
            if i_adjusted in self.open_idx['s']:
                output.write('%s%s' % (tag('s', 's'), brc('sbracket', '[')))
            if i_adjusted in self.open_idx['ng']:
                output.write('%s%s' % (tag('chunk', 'ng'), brc('bracket', '[')))
            if i_adjusted in self.open_idx['vg']:
                output.write('%s%s' % (tag('chunk', 'vg'), brc('bracket', '[')))
            output.write(text[i])
            if i_adjusted + 1 in self.close_idx['lex']:
                output.write(tag('lex', self.close_idx['lex'][i_adjusted + 1]))
            if i_adjusted + 1 in self.close_idx['ng']:
                output.write('%s%s' % (brc('bracket', ']'), tag('chunk', 'ng')))
            if i_adjusted + 1 in self.close_idx['vg']:
                output.write('%s%s' % (brc('bracket', ']'), tag('chunk', 'vg')))
            if i_adjusted + 1 in self.close_idx['s']:
                output.write('%s%s' % (brc('sbracket', ']'), tag('s', 's')))
        return output.getvalue()


class HTML(object):

    """Utility class for printing HTML to a file handle."""
    
    @classmethod
    def row(self, fh, elements):
        fh.write("<tr>\n")
        for e in elements:
            align = ' align=right' if isinstance(e, int) else ''
            fh.write("   <td%s>%s\n" % (align, e))
        fh.write("</tr>\n")



if __name__ == '__main__':

    options = ['run', 'comp' , 'diff',
               'gold=', 'system=', 'out=', 'display=', 'limit=']
    (opts, args) = getopt.getopt(sys.argv[1:], '', options)
    opts = { k:v for k,v in opts }

    gold = os.path.abspath(opts.get('--gold'))
    system = os.path.abspath(opts.get('--system'))
    limit = int(opts.get('--limit', sys.maxint))
    out = opts.get('--out')

    display = opts.get('--display')
    display_categories = [EXACT_MATCH, PARTIAL_MATCH, NO_MATCH_FP, NO_MATCH_FN]
    if display is None:
        display_choices = { c:True for c in display_categories }
    else:
        display_choices = { c:False for c in display_categories }
        for choice in display.split(','):
            display_choices[choice] = True

    if '--run' in opts:
        create_system_files_from_gold_standard(gold, system, limit)
    elif '--comp' in opts:
        compare_dirs(gold, system, limit)
    elif '--diff' in opts:
        view_differences(gold, system, out, display_choices, limit)

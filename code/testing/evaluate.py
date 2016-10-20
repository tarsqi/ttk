"""evaluate.py

Evaluation works by running the toolkit on gold standard files. These files can
either be enumerated or be given as a directory. Each file is loaded as a
TarsqiDocument and the gold tags are extracted, then the TagRepository of the
TarsqiDocument is reset and the code runs to recreate it. The last step is to
compare the newly created tag repository with the old one.

The input has to be ttk files.

"""

import os, sys

import copy
import path
import tarsqi
from library.main import LIBRARY

EVENT = LIBRARY.timeml.EVENT
TIMEX3 = LIBRARY.timeml.TIMEX
ALINK = LIBRARY.timeml.ALINK
SLINK = LIBRARY.timeml.SLINK
TLINK = LIBRARY.timeml.TLINK

LINK_TAGS = (ALINK, SLINK, TLINK)
TIMEML_TAGS = (EVENT, TIMEX3, ALINK, SLINK, TLINK)


def evaluate_dir(directory, limit=sys.maxint):
    fstats = []
    count = 0
    for fname in os.listdir(directory):
        count += 1
        if count > limit:
            break
        if fname.endswith('wsj_0907.tml'):
            continue
        print fname
        fstats.append(FileStatistics(os.path.join(directory, fname)))
    dstats = DirectoryStatistics(directory, fstats)
    dstats.pp()


def get_tags(fname):
    """Return two TagRepositories for fname, one with gold standard tags and one
    with system tags.  The tags in fname are consider the gold tags and they are
    extracted first. Then the TagRepositry will be reset and the toolkit will
    run over the file, creating a new repository."""
    # load the document, but do not run the pipeline
    tarsqi_inst, tarsqidoc = tarsqi.load_ttk_document(fname)
    gold_tags = copy.copy(tarsqidoc.tags)
    # before you reset, keep the docelement tags so that we do not have to rerun
    # the document parser
    docelement_tags = [t for t in tarsqidoc.tags.all_tags() if t.name == 'docelement']
    tarsqidoc.tags.reset()
    for tag in docelement_tags:
        tarsqidoc.tags.append(tag)
    tarsqidoc.tags.index()
    for (name, wrapper) in tarsqi_inst.pipeline:
        #print name
        tarsqi_inst._apply_component(name, wrapper, tarsqidoc)
    return gold_tags, tarsqidoc.tags


def get_annotations(tag_repository):
    """Return a list of offsets of all lex tags as well as a dictionary of the
    TimeML annotations in the tag repository."""
    timeml_tags = ('EVENT', 'TIMEX3', 'ALINK', 'SLINK', 'TLINK')
    annotations = { tagname: {} for tagname in timeml_tags }
    event_idx = {}
    timex_idx = {}
    for tag in tag_repository.all_tags():
        if tag.name == 'EVENT':
            event_idx[tag.attrs['eiid']] = tag
        elif tag.name == 'TIMEX3':
            timex_idx[tag.attrs['tid']] = tag
    for tag in tag_repository.all_tags():
        if tag.name in timeml_tags:
            offsets = get_offsets(tag, event_idx, timex_idx)
            if offsets is not None:
                annotations[tag.name][offsets] = tag.attrs
    return annotations


def get_offsets(tag, event_idx, timex_idx):
    """Get begin and end offsets for the tag. For an event or time, this is a pair
    of offsets, for example (13,16). For a link, this is pair of the offsets of
    the source and target of the link, for example ((13,16),(24,29))."""
    def retrieve_from_index(identifier):
        idx = event_idx if identifier[0] == 'e' else timex_idx
        try:
            return (idx[identifier].begin, idx[identifier].end)
        except KeyError:
            return (None, None)
    if tag.name in ('ALINK', 'SLINK', 'TLINK'):
        ids = (tag.attrs.get('timeID'),
               tag.attrs.get('eventInstanceID'),
               tag.attrs.get('relatedToTime'),
               tag.attrs.get('relatedToEventInstance'),
               tag.attrs.get('subordinatedEventInstance'))
        ids = [i for i in ids if i is not None]
        offsets = [retrieve_from_index(i) for i in ids if i is not None]
        if len(offsets) != 2:
            print "WARNING: unexpected offsets for %s" % tag.as_ttk_tag()
            return None
        elif offsets[0][0] is None or offsets[1][0] is None:
            print "WARNING: cannot root %s" % tag.as_ttk_tag()
            return None
        else:
            return tuple(offsets)
    else:
        return (tag.begin, tag.end)


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

    def __init__(self, filename):
        gold_tags, system_tags = get_tags(filename)
        self.filename = filename
        self.gold = get_annotations(gold_tags)
        self.system = get_annotations(system_tags)
        self.events = EntityStatistics(filename, EVENT, self.gold, self.system)
        self.timexes = EntityStatistics(filename, TIMEX3, self.gold, self.system)
        self.alinks = LinkStatistics(filename, ALINK, self.gold, self.system)
        self.slinks = LinkStatistics(filename, SLINK, self.gold, self.system)
        self.tlinks = LinkStatistics(filename, TLINK, self.gold, self.system)

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

    def __init__(self, filename, tagname, gold_annotations, system_annotations):
        self.filename = filename
        self.tagname = tagname
        self.gold = gold_annotations[tagname]
        self.system = system_annotations[tagname]
        self.tp = 0
        self.fp = 0
        self.fn = 0
        self._collect_counts()

    def _collect_counts(self):
        """Collect the counts for true positive, false positive and false negative."""
        for t in self.system.keys():
            if t in self.gold:
                self.tp += 1
            else:
                self.fp += 1
        for t in self.gold.keys():
            if t not in self.system:
                self.fn += 1

    def __str__(self):
        p = self.precision()
        r = self.recall()
        f= self.fscore()
        p = "%.2f" % p if p is not None else 'nil'
        r = "%.2f" % r if r is not None else 'nil'
        f = "%.2f" % f if f is not None else 'nil'
        return "<Statistics %s %s tp:%s fp:%s fn:%s precision=%s recall=%s f-score=%s>" % \
            (self.tagname, self.filename, self.tp, self.fp, self.fn, p, r, f)

    def precision(self):
        try:
            return float(self.tp) / (self.tp + self.fp)
        except ZeroDivisionError:
            return None

    def recall(self):
        try:
            return float(self.tp) / (self.tp + self.fn)
        except ZeroDivisionError:
            return None

    def fscore(self):
        p = self.precision()
        r = self.recall()
        if p is None or r is None:
            return None
        return (2 * p * r) / (p + r)


class LinkStatistics(object):

    def __init__(self, filename, tagname, gold_annotations, system_annotations):
        self.filename = filename
        self.tagname = tagname
        self.gold = gold_annotations[tagname]
        self.system = system_annotations[tagname]
        self.overlap = overlap(self.gold, self.system)
        #print self.gold.keys()
        #print self.system.keys()
        #print self.overlap
        self.correct = 0
        self.incorrect = 0
        for offset in self.overlap:
            if self.gold[offset]['relType'] == self.system[offset]['relType']:
                self.correct += 1
            else:
                self.incorrect += 1

    def __str__(self):
        accuracy = self.accuracy()
        astring = "nil" if accuracy is None else "%.2f" % accuracy
        return "<Statistics %s %s correct:%s incorrect:%s accuracy:%s>" % \
            (self.tagname, self.filename, self.correct, self.incorrect, astring)

    def accuracy(self):
        try:
            return float(self.correct) / (self.correct + self.incorrect)
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


def overlap(annotations1, annotations2):
    """Now just gets the keys that both have in common, should include links where
    source and target are reversed."""
    return [val for val in annotations1 if val in annotations2]



if __name__ == '__main__':
    gold_data = sys.argv[1]
    if os.path.isfile(gold_data):
        stats = Filestatistics(gold_data)
        print stats
    elif os.path.isdir(gold_data):
        limit = sys.argv[1] if len(sys.argv) > 2 else sys.maxint
        evaluate_dir(gold_data, limit)

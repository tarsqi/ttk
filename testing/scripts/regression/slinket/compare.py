"""compare.py

Compare two files with TTK link output, the first is considered the baseline and
the second the response. Compare the SLINKs on the begin and end offsets of the
events involved and check the SLINKs for the atributes listed in ATTRS.

At thispoint this script is only used for SLINKs.

There is overlap with the script with the same name in the evita test directory
and these files may be merged at some point.

Example usage:

   $ python compare.py data-out/wsj_0584.xml data-tmp/wsj_0584.xml

This gives a more usefull result than using a unix diff. With diff, if one file
has an extra event in the beginning, then all the other events will not match
anymore either because of the identifiers. This script just compares th eoffsets
of events and some of the link attributes and ignores identifiers.

Output shows elements in the baseline with <<< and elements in the current
system response with >>>. For each SLINK that is different the text where it
occurs is show as well as the ;link and the two events, here is an example (some
attributes removed from the event for readability):

<<<  4601-4609-4643-4647
     finds the BellSouth [proposal still flawed because the company does] n't have to wait fi
     <SLINK eventInstanceID="ei110" relType="MODAL" subordinatedEventInstance="ei112" />
        <EVENT begin="4601" end="4609" class="OCCURRENCE" eid="e110" eiid="ei110" form="proposal" />
        <EVENT begin="4643" end="4647" class="OCCURRENCE" eid="e112" eiid="ei112" form="does" />
>>>  4601-4609-4660-4664
     finds the BellSouth [proposal still flawed because the company does n't have to wait] five years to begin
     <SLINK eventInstanceID="ei110" relType="MODAL" subordinatedEventInstance="ei113" />
        <EVENT begin="4601" end="4609" class="OCCURRENCE" eid="e110" eiid="ei110" form="proposal" />
        <EVENT begin="4660" end="4664" class="OCCURRENCE" eid="e113" eiid="ei113" form="wait" />

"""

# TODO: this does not yet deal with ALINKs
# TODO: how about highlighting the differences in the diff
# TODO: and how about highlighting the events in the fragment


import sys

from xml.dom.minidom import parse


ATTRS = ('relType', 'syntax')


def compare_files(fname1, fname2):
    dom1 = parse(fname1)
    dom2 = parse(fname2)
    text1 = dom1.getElementsByTagName('text')[0].firstChild.data
    text2 = dom2.getElementsByTagName('text')[0].firstChild.data
    events1 = dom1.getElementsByTagName('EVENT')
    events2 = dom2.getElementsByTagName('EVENT')
    events1_idx = index_on_eiid(events1)
    events2_idx = index_on_eiid(events2)
    slinks1 = dom1.getElementsByTagName('SLINK')
    slinks2 = dom2.getElementsByTagName('SLINK')
    slinks1_idx = group_on_offsets(slinks1, events1_idx)
    slinks2_idx = group_on_offsets(slinks2, events2_idx)
    result = []
    for offsets in difference(slinks1_idx.keys(), slinks2_idx.keys()):
        result.append([offsets, "<<<"] + slinks1_idx[offsets])
    for offsets in difference(slinks2_idx.keys(), slinks1_idx.keys()):
        result.append([offsets, ">>>"] + slinks2_idx[offsets])
    for offsets in intersection(slinks1_idx.keys(), slinks2_idx.keys()):
        link1 = slinks1_idx[offsets][0]
        link2 = slinks2_idx[offsets][0]
        for attr in ATTRS:
            if link1.getAttribute(attr) != link2.getAttribute(attr):
                result.append([offsets, '<<<'] + slinks1_idx[offsets])
                result.append([offsets, '>>>'] + slinks2_idx[offsets])
    print_results(result, text1)
    
def group_on_offsets(slinks, events_idx):
    result = {}
    for slink in slinks:
        eiid1 = slink.getAttribute('eventInstanceID')
        eiid2 = slink.getAttribute('subordinatedEventInstance')
        e1 = events_idx[eiid1]
        e2 = events_idx[eiid2]
        offsets = "%s-%s-%s-%s" % (e1.getAttribute('begin'), e1.getAttribute('end'),
                                   e2.getAttribute('begin'), e2.getAttribute('end'))
        result[offsets] = [slink, e1, e2]
    return result

def index_on_eiid(events):
    idx = {}
    for event in events:
        idx[event.getAttribute('eiid')] = event
    return idx

def difference(l1, l2):
    return list(set(l1) - set(l2))

def intersection(l1, l2):
    return list(set(l1) & set(l2))

def node_as_string(node):
    return "%s" % node.toprettyxml().strip()

def print_results(diffs, text):
    for (offsets, direction, slink, e1, e2) in sorted(diffs):
        offsets2 = [int(offs) for offs in offsets.split('-')]
        p1 = max(0, min(offsets2))
        p2 = max(offsets2)
        left_context = text[p1-20:p1]
        right_context = text[p2:p2+20]
        fragment = text[p1:p2]
        print "%s  %s" % (direction, offsets)
        print "     %s[%s]%s" % (left_context, fragment, right_context)
        print "     %s" % node_as_string(slink)
        print "        %s" % node_as_string(e1)
        print "        %s" % node_as_string(e2)
    if diffs:
        print "%d differences in %d lines" % (len(diffs), len(text.split("\n")))


if __name__ == '__main__':
    fname1 = sys.argv[1]
    fname2 = sys.argv[2]
    compare_files(fname1, fname2)

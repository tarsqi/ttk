"""compare.py

Compare two files with TTK entity output, the first is considered the baseline
and the second the response. Compare them for the tags listed in TAGS and the
ATTRIBUTES listed in ATTRS.

This script is used pretty much only for comparing the events and chunks in
Evita output.

Example usage:

   $ python compare.py data-out/evita-BE.xml data-tmp/evita-BE.xml

This gives a more usefull result than using a unix diff. With diff, if one file
has an extra event in the beginning, then all the other events will not match
anymore either because of the identifiers. This script just compares some of the
attributes and ignores identifiers.

Output is similar to the diff output, here is an example (some attributes
removed from the event for readability):

   <  <vg begin="308" end="316" id="c28"/>  text='are also'
   >  <vg begin="308" end="323" id="c28"/>  text='are also coming'
   <  <ng begin="317" end="328" id="c29"/>  text='coming home'
   >  <ng begin="324" end="328" id="c29"/>  text='home'
   >  <EVENT begin="317" eid="e8" eiid="ei8" end="323" pos="VERB" />  text='coming'
   5 differences in 87 lines

The output gives tags in the baseline after < and tags in the response after > and for
each of them it gives the text span in the primary data.

This does generate some sub-optimal output if one of the files has multiple
occurrences of the same tag name with the same begin and end.

"""

import sys

from xml.dom.minidom import parse


TAGS = ('vg', 'ng', 'EVENT')
ATTRS = ('begin', 'end', 'class', 'tense', 'aspect', 'modality', 'polarity')


def compare_files(fname1, fname2):
    dom1 = parse(fname1)
    dom2 = parse(fname2)
    text1 = dom1.getElementsByTagName('text')[0].firstChild.data
    text2 = dom2.getElementsByTagName('text')[0].firstChild.data
    result = []
    for tag in TAGS:
        tags1 = dom1.getElementsByTagName(tag)
        tags2 = dom2.getElementsByTagName(tag)
        tags1_idx = group_on_start(tags1)
        tags2_idx = group_on_start(tags2)
        for begin in difference(tags1_idx.keys(), tags2_idx.keys()):
            result.append([begin, "<  " + node_as_string(tags1_idx[begin], text1)])
        for begin in difference(tags2_idx.keys(), tags1_idx.keys()):
            result.append([begin, ">  " + node_as_string(tags2_idx[begin], text2)])
        for begin in intersection(tags1_idx.keys(), tags2_idx.keys()):
            n1 = tags1_idx[begin]
            n2 = tags2_idx[begin]
            for attr in ATTRS:
                if n1.getAttribute(attr) != n2.getAttribute(attr):
                    result.append([begin, '<  ' + node_as_string(n1, text1)])
                    result.append([begin, '>  ' + node_as_string(n2, text2)])
    print_results(result, text1)

def group_on_start(node_list):
    result = {}
    for node in node_list:
        # there is an assumption here that in a file two tags with the same
        # tagnames will never have the same begin offset
        begin = node.getAttribute('begin')
        result[begin] = node
    return result

def difference(l1, l2):
    return list(set(l1) - set(l2))

def intersection(l1, l2):
    return list(set(l1) & set(l2))

def node_as_string(node, text):
    begin = int(node.getAttribute('begin'))
    end = int(node.getAttribute('end'))
    return "%s  text='%s'" % (node.toprettyxml().strip(), text[begin:end])

def print_results(diffs, text):
    for diff in sorted(diffs):
        print diff[1]
    if diffs:
        print "%d differences in %d lines" % (len(diffs), len(text.split("\n")))


if __name__ == '__main__':
    fname1 = sys.argv[1]
    fname2 = sys.argv[2]
    compare_files(fname1, fname2)

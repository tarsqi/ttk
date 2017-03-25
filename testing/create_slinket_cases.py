"""create_slinket_cases.py

Code to create Slinket unit test cases. Runs by taking all SLINKs from a
Timebank parse and put them in files, one for each SLINK relType, as potential
test cases. Files are named slink-cases-RELTYPE.txt, where RELTYPE stands for
one of the relation types.

The output files have lines like

('MODAL', 'ABC19980120.1830.0957.xml', 'toClause3', (13,20), (34,38),
 "Fidel Castro invited John Paul to come for a reason.")

which can be inserted directly as unit tests in SlinketTest.

Running this script will actually report a lot of errors and warnings, but
useful output is created and fixing the errors is low priority.

"""

import os, sys, codecs
from xml.dom.minidom import parse, parseString


TIMEBANK_DIR = '../data/out/timebank'
TTK_FILE = '../out-slinket.xml'

SLINK_CASES = {}


def parse_directory(dname):
    #for (counter, fname) in os.listdir(dname):
    for fname in os.listdir(dname):
        # if counter > 10: break
        sys.stderr.write("%s\n" % fname)
        try:
            parse_file(os.path.join(dname, fname))
        except:
            sys.stderr.write("ERROR on %s\n" % fname)

def parse_file(fname):
    dom = parse(fname)
    text = dom.getElementsByTagName('text')[0]
    source_tags = dom.getElementsByTagName('source_tags')[0]
    try:
        tarsqi_tags = dom.getElementsByTagName('tarsqi_tags')[0]
    except IndexError:
        # some older parsed files still have ttk_tags, allow for that
        tarsqi_tags = dom.getElementsByTagName('ttk_tags')[0]
    sentences = tarsqi_tags.getElementsByTagName('s')
    events = tarsqi_tags.getElementsByTagName('EVENT')
    slinks = tarsqi_tags.getElementsByTagName('SLINK')
    source_text = text.firstChild.data
    parse_slinks(os.path.basename(fname), slinks, events, sentences, source_text)

def parse_slinks(fname, slinks, events, sentences, source_text):
    event_dict = {}
    for event in events:
        eiid = event.getAttribute('eiid')
        event_dict[eiid] = event
    for slink in slinks:
        parse_slink(fname, slink, event_dict, sentences, source_text)
    for reltype in SLINK_CASES.keys():
        fh = codecs.open("slink-cases-%s.txt" % reltype, 'w')
        for case in SLINK_CASES[reltype]:
            fh.write(case)

def parse_slink(fname, slink, event_dict, sentences, source_text):
    rel = slink.getAttribute('relType')
    rule = slink.getAttribute('syntax')
    e1 = slink.getAttribute('eventInstanceID')
    e2 = slink.getAttribute('subordinatedEventInstance')
    e1p1 = int(event_dict[e1].getAttribute('begin'))
    e1p2 = int(event_dict[e1].getAttribute('end'))
    e2p1 = int(event_dict[e2].getAttribute('begin'))
    e2p2 = int(event_dict[e2].getAttribute('end'))
    event_text1 = source_text[e1p1:e1p2]
    event_text2 = source_text[e2p1:e2p2]
    enclosing_sentence = None
    for s in sentences:
        if int(s.getAttribute('begin')) <= e1p1 and int(s.getAttribute('end')) >= e1p1:
            enclosing_sentence = s
    s_p1 = int(enclosing_sentence.getAttribute('begin'))
    s_p2 = int(enclosing_sentence.getAttribute('end'))
    sentence_text = source_text[s_p1:s_p2]
    sentence_text = ' '.join(sentence_text.split())
    (e1p1, e1p2) = get_local_offset(sentence_text, event_text1)
    (e2p1, e2p2) = get_local_offset(sentence_text, event_text2)
    if e1p1 < 0:
        sys.stderr.write("WARNING: did not find '%s' in '%s'\n" % (event_text1, sentence_text))
    elif e2p1 < 0:
        sys.stderr.write("WARNING: did not find '%s' in '%s'\n" % (event_text2, sentence_text))
    else:
        case = "('%s', '%s', '%s', (%s,%s), (%s,%s),\n \"%s\")\n" \
               % (rel, fname, rule, e1p1, e1p2, e2p1, e2p2, sentence_text)
        SLINK_CASES.setdefault(rel,[]).append(case)

def get_local_offset(sentence, text):
    idx1 = sentence.find(text)
    idx2 = idx1 + len(text)
    return (idx1, idx2)


if __name__ == '__main__':

    #parse_file(TTK_FILE)
    parse_directory(TIMEBANK_DIR)

